import logging
from os import path

from beaker.middleware import SessionMiddleware
from paste.registry import RegistryManager
from werkzeug import SharedDataMiddleware, DebuggedApplication
from werkzeug.exceptions import HTTPException, InternalServerError
from werkzeug import create_environ

from pysutils.datastructures import BlankObject
from pysutils.strings import randchars
from pysmvt import settings, ag, session, rg, user, routing, config, _getview
from pysmvt.exceptions import ForwardException, ProgrammingError
from pysmvt.mail import mail_programmers
from pysmvt.users import User
from pysmvt.utils import randhash, Context, exception_with_context
from pysmvt.wrappers import Request

log = logging.getLogger(__name__)

class Application(object):
    
    def __init__(self):
        self._id = randhash()
    
        # keep local copies of these objects around for later
        # when we need to bind them to the request
        self.settings = settings._current_obj()
        self.ag = ag._current_obj()
    
    def start_request(self, environ=None):
        rg._push_object(Context())
        
        # create a fake environment if needed
        if not environ:
            environ = create_environ('/[pysmvt_test]')
        
        # this might throw an exception, but we are letting that go
        # b/c we need to make sure the url adapter gets created
        rg.urladapter = ag.route_map.bind_to_environ(environ)
    
    def console_dispatch(self, callable, environ=None):
        self.start_request(environ)
        try:
            callable()
        finally:
            self.end_request()
    
    def end_request(self):
        rg._pop_object()

class RequestManager(object):
    def __init__(self, app, environ):
        self.app = app
        self.environ = environ
        
    def registry_setup(self):
        environ = self.environ
        environ['paste.registry'].register(settings, self.app.settings)
        environ['paste.registry'].register(ag, self.app.ag)
        if environ.has_key('beaker.session'):
            environ['paste.registry'].register(session, environ['beaker.session'])
            environ['paste.registry'].register(user, self.user_setup())
        else:
            environ['paste.registry'].register(session, None)
            environ['paste.registry'].register(user, None)
        environ['paste.registry'].register(rg, BlankObject())
    
    def rg_setup(self):
        # WSGI request setup
        rg.ident = randchars()
        rg.environ = self.environ
        # the request object binds itself to rg.request
        Request(self.environ)
    
    def routing_setup(self):
        rg.urladapter = ag.route_map.bind_to_environ(self.environ)
    
    def user_setup(self):
        environ = self.environ
        try:
            return environ['beaker.session'].setdefault('__pysmvt_user', User())
        except KeyError, e:
            if '__pysmvt_user' not in str(e):
                raise
            environ['beaker.session']['__pysmvt_user'] = User()
            return environ['beaker.session']['__pysmvt_user']

    def __enter__(self):
        self.registry_setup()
        self.rg_setup()
        self.routing_setup()
        # allow middleware higher in the stack to help initilize the request
        # after the registry variables have been setup
        if 'pysmvt.request_setup' in self.environ:
            for callable in self.environ['pysmvt.request_setup']:
                callable()

    def __exit__(self, exc_type, exc_value, tb):
        if 'pysmvt.request_teardown' in self.environ:
            for callable in self.environ['pysmvt.request_teardown']:
                callable()
        
class ResponseContext(object):
    def __init__(self, error_doc_code):
        self.environ = rg.environ
        self.respview = None
        self.error_doc_code = error_doc_code
        self.css = []
        self.js = []

    def __enter__(self):
        rg.respctx = self
        # allow middleware higher in the stack to help initilize the response
        if 'pysmvt.response_setup' in self.environ:
            for callable in self.environ['pysmvt.response_setup']:
                callable()

    def __exit__(self, exc_type, e, tb):
        if 'pysmvt.response_teardown' in self.environ:
            for callable in self.environ['pysmvt.response_teardown']:
                callable()
        if isinstance(e, ForwardException):
            log.debug('forwarding to %s (%s)', e.forward_endpoint, e.forward_args)
            rg.forward_queue.append((e.forward_endpoint, e.forward_args))
            if len(rg.forward_queue) == 10:
                raise ProgrammingError('forward loop detected: %s' % '->'.join([g[0] for g in rg.forward_queue]))
            return True
        if 'beaker.session' in self.environ:
            self.environ['beaker.session'].save()

class WSGIApplication(Application):

    def __init__(self):
        Application.__init__(self)
    
    def request_manager(self, environ):
        return RequestManager(self, environ)
        
    def response_context(self, error_doc_code):
        return ResponseContext(error_doc_code)
        
    def response_cycle(self, endpoint, args, called_from=None, error_doc_code=None):
        rg.forward_queue = [(endpoint, args)]
        while True:
            with self.response_context(error_doc_code):
                endpoint, args = rg.forward_queue[-1]
                return self.dispatch_to_view(endpoint, args, called_from)

    def dispatch_to_view(self, endpoint, args, called_from=None):
        if len(rg.forward_queue) > 1:
            called_from = 'forward'
        else:
            called_from = called_from or 'client'
        log.debug('dispatch to %s (%s)', endpoint, args)
        return _getview(endpoint, args, called_from)

    def wsgi_app(self, environ, start_response):
        with self.request_manager(environ):
            try:
                endpoint, args = rg.urladapter.match()
                log.debug('wsgi_app processing %s (%s)', endpoint, args)
                response = self.response_cycle(endpoint, args)
            except HTTPException, e:
                response = self.handle_http_exception(e)
            except Exception, e:
                response = self.handle_exception(e)
            return response(environ, start_response)
    
    def handle_http_exception(self, e):
        """Handles an HTTP exception.  By default this will invoke the
        registered error handlers and fall back to returning the
        exception as response.

        .. versionadded: 0.3
        """
        endpoint = settings.error_docs.get(e.code)
        log.debug('handling http exception %s with %s', e, endpoint)
        if endpoint is None:
            return e
        try:
            return self.response_cycle(endpoint, {}, 'error docs', error_doc_code=e.code)
        except HTTPException, httpe:
            log.debug('error doc endpoint %s raised HTTPException: %s', endpoint, httpe)
            # the document handler is bad, so send back the original exception
            return e
        except Exception, exc:
            log.debug('error doc endpoint %s raised exception: %s', endpoint, exc)
            return self.handle_exception(exc)
    
    def handle_exception(self, e):
        """Default exception handling that kicks in when an exception
        occours that is not catched.  In debug mode the exception will
        be re-raised immediately, otherwise it is logged an the handler
        for an 500 internal server error is used.  If no such handler
        exists, a default 500 internal server error message is displayed.

        .. versionadded: 0.3
        """
        log.error('exception encountered: %s' % exception_with_context())
        if not settings.exception_handling:
            raise
        if 'email' in settings.exception_handling:
            try:
                mail_programmers('exception encountered', exception_with_context())
            except Exception, e:
                log.exception('exception when trying to email exception')
        if 'format' in settings.exception_handling:
            response = InternalServerError()
            response.description = '<pre>%s</pre>' % escape(exception_with_context())
            return response
        if 'handle' in settings.exception_handling:
            endpoint = settings.error_docs.get(500)
            if endpoint is None:
                # turn the exception into a 500 server response
                log.debug('handling exception with generic 500 response')
                return InternalServerError()
            else:
                log.debug('handling exception with error doc endpoint %s' % endpoint)
                try:
                    return self.response_cycle(endpoint, {}, 'error docs', error_doc_code=500)
                except HTTPException, httpe:
                    log.debug('error doc endpoint %s raised HTTPException: %s', endpoint, httpe)
                except Exception, exc:
                    log.exception('error doc endpoint %s raised exception:', endpoint)
                # the document handler is bad, so give a generic response
                return InternalServerError()
        raise

    def __call__(self, environ, start_response):
        return self.wsgi_app(environ, start_response)

def full_wsgi_stack(appklass=WSGIApplication):
    """
        returns the WSGIApplication wrapped in common middleware
    """
    app = appklass()
    
    settings = app.settings
    
    if settings.beaker.enabled:
        app = SessionMiddleware(app, **dict(settings.beaker))
    
    app = RegistryManager(app)
    
    # serve static files from main app and supporting apps (need to reverse order b/c
    # middleware stack is run in bottom up order).  This works b/c if a
    # static file isn't found, the ShardDataMiddleware just forwards the request
    # to the next app.
    if settings.static_files.enabled:
        for appname in config.appslist(reverse=True):
            app_py_mod = __import__(appname)
            fs_static_path = path.join(path.dirname(app_py_mod.__file__), 'static')
            static_map = {routing.add_prefix('/') : fs_static_path}
            app = SharedDataMiddleware(app, static_map)
    
    # show nice stack traces and debug output if enabled
    if settings.debugger.enabled:
        app = DebuggedApplication(app, evalex=settings.debugger.interactive)
    
    # log http requests, use sparingly on production servers
    if settings.logs.http_requests.enabled:
        app = HttpRequestLogger(app, True,
                settings.logs.http_requests.filters.path_info,
                settings.logs.http_requests.filters.request_method)
    
    return app

def minimal_wsgi_stack(appklass=WSGIApplication):
    """
        returns the WSGIApplication wrapped in minimal middleware, mostly useful
        for internal testing
    """
    app = appklass()
    app = RegistryManager(app)
    return app