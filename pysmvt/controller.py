from os import path
import sys
from traceback import format_exc
from pysmvt.wrappers import Request, Response
from pysmvt.exceptions import RedirectException, ForwardException, ProgrammingError
from pysmvt.user import SessionUser
from pysmvt.mail import mail_programmers
from pysmvt import routing
from werkzeug import ClosingIterator, SharedDataMiddleware, MultiDict
from werkzeug.routing import Map, Submount, RequestRedirect
from werkzeug.exceptions import HTTPException, NotFound, InternalServerError, \
    MethodNotAllowed
import werkzeug.utils
from werkzeug.debug import DebuggedApplication
from beaker.middleware import SessionMiddleware

from pysmvt.application import request_context as rc
from pysmvt.application import request_context_manager as rcm

from pysmvt.database import get_dbsession, get_dbsession_cls
from pysmvt.utils import randchars, traceback_depth, log_info, log_debug, pprint

# Note: this controller is only instantiated per-process, not per request.
# Therefore, anything that needs to be initialized per application/per process
# can go in __init__, but anything that needs to be initialized per request
# needs to go in dispatch_request()
class Controller(object):
    """
    The controller is responsible for handling the request and responding
    appropriately
    """

    def __init__(self):
        rc.controller = self
        
        # Routing Map
        self._route_map = Map()
        
        # load routes from the application and settings files
        self._init_routes()

        self._setup_middleware()

    def bind_to_context(self):
        """
        Useful for the shell.  Binds the application to the current active
        context.  It's automatically called by the shell command.
        """
        rc.controller = self

    def dispatch_request(self, environ, start_response):
        """
            Dispatch an incoming request.  It looks like this:
            - wsgi request setup
                - response handling (loop)
                    - non-200 response handler
                        - exception handler (env, endpoint, args)
                            - client request init -> endpoint & args
                                - forward()
                                    - call view
                                + response cleanup
                        + catch exceptions
                            -- determine context (normal, xmlhttprequest)
                            -- turn HttpExceptions into response objects
                            -- handle based on context settings
                                -- propogate
                                -- turn into 500
                                -- log
                                -- email
                                -- stack trace
                                -- interactive stack trace
                    + catch non-200 responses
                        -- determine context (normal, xmlhttprequest)
                        -- handle based on context settings
                            -- pretty: endpoint & args -> exception handler
                            -- minimal: pass-through
                            -- json: convert response description to JSON
            + wsgi request cleanup
        """
        
        # WSGI request setup
        self.bind_to_context()
        rc.ident = randchars()
        rc.environ = environ
        request = Request(environ)
        rc.session = environ['beaker.session']
        self._setup_user()

        try:
            response = self._error_documents_handler(environ)
            return response(environ, start_response)
        finally:
            # save the user session
            rc.session.save()

            # handle context local cleanup
            rcm.cleanup()
    
    def _error_documents_handler(self, environ):
        response = orig_resp = self._exception_handing('client', environ)
        def get_status_code(response):
            if isinstance(response, HTTPException):
                return response.code
            else:
                return response.status_code
        code = get_status_code(response)
        if code in rc.application.settings.error_docs:
            handling_endpoint = rc.application.settings.error_docs.get(code)
            rc.application.logger.info('error docs: handling code %d with %s' % (code, handling_endpoint))
            new_response = self._exception_handing('error docs', endpoint=handling_endpoint)
            # only take the new response if it completed succesfully.  If not,
            # then we should just return the original response after logging the
            # error
            if get_status_code(new_response) == 200:
                try:
                    new_response.status_code = code
                except AttributeError, e:
                    if "object has no attribute 'status_code'" not in str(e):
                        raise
                    new_response.code = code
                response = new_response
            else:
                rc.application.logger.debug('error docs: encountered non-200 status code response '
                        '(%d) when trying to handle with %s' % (get_status_code(new_response), handling_endpoint))
        if isinstance(response, HTTPException):
            messages = rc.user.get_messages()
            if messages:
                msg_html = ['<h2>Error Details:</h2><ul>']
                for msg in messages:
                    msg_html.append('<li>(%s) %s</li>' % (msg.severity, msg.text))
                msg_html.append('</ul>')
                response.description = response.description + '\n'.join(msg_html)
        return response
    
    def _exception_handing(self, called_from, environ = None, endpoint=None, args = {}):
        try:
            if environ:
                endpoint, args = self._endpoint_args_from_env(environ)
            response = self._inner_requests_wrapper(endpoint, args, called_from)
        except HTTPException, e:
            rc.application.logger.info('exception handling caught HTTPException "%s", sending as response' % e.__class__.__name__)
            response = e
        except RedirectException, e:
            rc.application.logger.info('exception handling caught RedirectException')
            response = rc.response
        except Exception, e:
            if rc.application.settings.exceptions.log:
                rc.application.logger.debug('exception handling: %s' % str(e))
            if rc.application.settings.exceptions.email:
                trace = format_exc()
                envstr = pprint(rc.environ, 4, True)
                mail_programmers('exception encountered', '== TRACE ==\n\n%s\n\n== ENVIRON ==\n\n%s' % (trace, envstr))
            if rc.application.settings.exceptions.hide:
                # turn the exception into a 500 server response
                response = InternalServerError()
            else:
                raise
        return response
    
    def _endpoint_args_from_env(self, environ):
        try:
            # bind the route map to the current environment
            urls = rc.urladapter = self._route_map.bind_to_environ(environ)
            
            # initialize endpoint to avoid UnboundLocalError
            endpoint = None
            
            # find the requested view based on the URL
            return urls.match()
        
        except (NotFound, MethodNotAllowed, RequestRedirect):
            if endpoint is None:
                rc.application.logger.info('URL (%s) generated HTTPException' % environ['PATH_INFO'])
            raise
    
    def _inner_requests_wrapper(self, endpoint, args, called_from):
        # this loop allows us to handle forwards
        rc.forward_queue = [(endpoint, args)]
        while True:
            rc.response = None
            rc.respview = None
            try: 
                # call the view
                endpoint, args = rc.forward_queue[-1]
                response = self._call_view(endpoint, args, called_from)
                if not isinstance(response, Response):
                    raise ProgrammingError('view %s did not return a response object' % endpoint)
                return response
            except ForwardException:
                called_from = 'forward'
            finally:                
                # rollback any uncommitted database transactions.  We assume that
                # an explicit commit will be issued and anything leftover was accidental
                get_dbsession().rollback()
                
                # make sure we get a new DB session for the next request
                get_dbsession_cls().remove()
    
    def redirect(self, location, permanent=False, code=302 ):
        """
            location: URI to redirect to
            permanent: if True, sets code to 301 HTTP status code
            code: allows 303 or 307 redirects to be sent if needed, see
                http://www.w3.org/Protocols/rfc2616/rfc2616-sec10.html
        """
        if permanent:
            code = 301
        rc.response = werkzeug.utils.redirect(location, code)
        raise RedirectException()
    
    def forward(self, endpoint, args = {}):
        if len(rc.forward_queue) == 10:
            raise ProgrammingError('forward loop detected: %s' % '->'.join([g[0] for g in rc.forward_queue]))
        rc.forward_queue.append((endpoint, args))
        raise ForwardException
    
    def __call__(self, environ, start_response):
        """Just forward a WSGI call to the first internal middleware."""
        return self._dispatch(environ, start_response)
    
    def _init_routes(self):
        """ add routes to the main Map object from the application settings and
            from module settings """
       
        # application routes
        self._add_routing_rules(rc.application.settings.routing.routes)
       
        # module routes        
        for module in rc.application.settings.modules.keys():
            try:
                rc.application.loader.appmod_names('%s.settings' % module, 'Settings', globals())
                s = Settings()
                # load the routes from the module
                self._add_routing_rules(s.routes)
            except ImportError, e:
                # check the exception depth to make sure the import
                # error we caught was just a missing .settings
                _, _, tb = sys.exc_info()
                # 3 = .settings wasn't found
                if traceback_depth(tb) in [3] or 'cannot import name routes' in str(e):
                    pass
                else:
                    raise
    
    def _add_routing_rules(self, rules):
        try:
            if len(rc.application.settings.routing.prefix) > 1:
                # prefix the routes with the prefix in the app settings class
                from werkzeug.routing import Submount
                self._route_map.add(Submount( rc.application.settings.routing.prefix, rules ))
            else:
                raise AttributeError
        except AttributeError:
            for rule in rules or ():
                self._route_map.add(rule)
    
    def call_view(self, endpoint, **kwargs):
        return self._call_view(endpoint, kwargs, 'call_view')
    
    def _call_view(self, endpoint, args, called_from ):
        """
            called_from options: client, forward, call_view, template
        """
        from pysmvt.view import RespondingViewBase
        
        app_mod_name, vclassname = endpoint.split(':')
        
        try:
            vklass = rc.application.loader.appmod_names('%s.views' % app_mod_name, vclassname)
            if called_from in ('client', 'forward', 'error docs'):
                if not issubclass(vklass, RespondingViewBase):
                    if called_from == 'client':
                        raise ProgrammingError('Route exists to non-RespondingViewBase view "%s"' % vklass.__name__)
                    elif called_from == 'error docs':
                        raise ProgrammingError('Error document handling endpoint used non-RespondingViewBase view "%s"' % vklass.__name__)
                    else:
                        raise ProgrammingError('forward to non-RespondingViewBase view "%s"' % vklass.__name__)
        except ImportError, e:
            # if we find the module_to_load in the exception message,
            # we know the exception was thrown b/c that module
            # could not be loaded.  Otherwise, its probably an import
            # error from the view module and we want that propogated
            _, _, tb = sys.exc_info()
            # 2 = view class name wasn't found
            # 3 = view module wasn't found
            if traceback_depth(tb) in (2,3):
                msg = 'Could not load view "%s": %s' % (endpoint, str(e))
                rc.application.logger.debug(msg)
                raise ProgrammingError(msg)
            raise
        
        vmod_dir = path.dirname(sys.modules[vklass.__module__].__file__)
        
        # combine URL arguments and GET arguments into a single MultiDict
        # of arguments
        oView = vklass(vmod_dir, endpoint, args )
        return oView()
    
    def _setup_middleware(self):
        # apply our middlewares.   we apply the middlewars *inside* the
        # application and not outside of it so that we never lose the
        # reference to our application object.
        
        # last WSGI app to be called is our controllers dispatch_request function
        self._dispatch = self.dispatch_request

        # session middleware
        self._setup_session_middleware()
        
        # handle context locals
        self._dispatch = rcm.make_middleware(self._dispatch)
                
        # handles all of our static documents (CSS, JS, images, etc.)
        self._setup_static_middleware()
        
        # handle debugging exceptions, this is called first to catch
        # as many problems as possible
        self._setup_debug_middleware()
    
    def _setup_debug_middleware(self):
        if rc.application.settings.debugger.enabled:
            if rc.application.settings.debugger.format == 'interactive':
                evalex=True
            else:
                evalex=False
            self._dispatch = DebuggedApplication(self._dispatch, evalex=evalex)
    
    def _setup_static_middleware(self):
        static_map = {
            routing.add_prefix('/static'):     rc.application.staticDir
        }
        for app in rc.application.settings.supporting_apps:
            app_py_mod = rc.application.loader.app(app)
            fs_static_path = path.join(path.dirname(app_py_mod.__file__), 'static')
            static_map[routing.add_prefix('/%s/static' % app)] = fs_static_path
        self._dispatch = SharedDataMiddleware( self._dispatch, static_map)
    
    def _setup_session_middleware(self):
        self._dispatch = SessionMiddleware(self._dispatch, **dict(rc.application.settings.beaker))

    def _setup_user(self):
        rc.user = SessionUser()
