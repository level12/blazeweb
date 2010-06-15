import logging

from blazeutils.datastructures import BlankObject
from blazeutils.strings import randchars, randhash
from werkzeug.exceptions import HTTPException, InternalServerError
from werkzeug import create_environ
from werkzeug.routing import Map, Submount

import blazeweb
from blazeweb.exceptions import Forward, ProgrammingError, Redirect
from blazeweb.hierarchy import findobj, HierarchyImportError, \
    listplugins, visitmods, findview, split_endpoint
from blazeweb.logs import create_handlers_from_settings
from blazeweb.mail import mail_programmers
from blazeweb.templating import default_engine
from blazeweb.users import User
from blazeweb.utils import exception_with_context
from blazeweb.utils.filesystem import mkdirs, copy_static_files
from blazeweb.views import _RouteToTemplate
from blazeweb.wrappers import Request

log = logging.getLogger(__name__)

class RequestManager(object):
    def __init__(self, app, environ):
        self.app = app
        self.environ = environ

    def registry_setup(self):
        environ = self.environ
        environ['paste.registry'].register(blazeweb.rg, BlankObject())
        environ['paste.registry'].register(blazeweb.settings, self.app.settings)
        environ['paste.registry'].register(blazeweb.ag, self.app.ag)
        environ['paste.registry'].register(blazeweb.user, self.user_setup())

    def rg_setup(self):
        blazeweb.rg.ident = randchars()
        blazeweb.rg.environ = self.environ
        # the request object binds itself to rg.request
        Request(self.environ)
        if self.environ.has_key('beaker.session'):
            blazeweb.rg.session = self.environ['beaker.session']
            log.debug('beaker session found, id: %s', blazeweb.rg.session.id)
        else:
            blazeweb.rg.session = None

    def routing_setup(self):
        blazeweb.rg.urladapter = blazeweb.ag.route_map.bind_to_environ(self.environ)

    def user_setup(self):
        environ = self.environ
        if 'beaker.session' in environ:
            if '__blazeweb_user' not in environ['beaker.session']:
                environ['beaker.session']['__blazeweb_user'] = User()
            return environ['beaker.session']['__blazeweb_user']
        # having a user object that is not in a session makes sense for testing
        # purposes, but probably not in production use
        return User()

    def __enter__(self):
        self.registry_setup()
        self.rg_setup()
        self.routing_setup()
        # allow middleware higher in the stack to help initilize the request
        # after the registry variables have been setup
        if 'blazeweb.request_setup' in self.environ:
            for callable in self.environ['blazeweb.request_setup']:
                callable()

    def __exit__(self, exc_type, exc_value, tb):
        if 'blazeweb.request_teardown' in self.environ:
            for callable in self.environ['blazeweb.request_teardown']:
                callable()

class ResponseContext(object):
    def __init__(self, error_doc_code):
        self.environ = blazeweb.rg.environ
        # this gets set if this response context is initilized b/c
        # an error document handler is being called.  It allows the View
        # that handles the error code to know what code it is being called
        # for.
        self.error_doc_code = error_doc_code

    def __enter__(self):
        log.debug('enter response context')
        blazeweb.rg.respctx = self
        # allow middleware higher in the stack to help initilize the response
        if 'blazeweb.response_cycle_setup' in self.environ:
            for callable in self.environ['blazeweb.response_cycle_setup']:
                callable()

    def __exit__(self, exc_type, e, tb):
        log.debug('exit response context started')
        if 'blazeweb.response_cycle_teardown' in self.environ:
            for callable in self.environ['blazeweb.response_cycle_teardown']:
                callable()
        if isinstance(e, Forward):
            log.debug('forwarding to %s (%s)', e.forward_endpoint, e.forward_args)
            blazeweb.rg.forward_queue.append((e.forward_endpoint, e.forward_args))
            if len(blazeweb.rg.forward_queue) == 10:
                raise ProgrammingError('forward loop detected: %s' % '->'.join([g[0] for g in blazeweb.rg.forward_queue]))
            return True
        if 'beaker.session' in self.environ:
            self.environ['beaker.session'].save()
        log.debug('exit response context finished')

class WSGIApp(object):

    def __init__(self, module_or_settings, profile=None):
        self._id = randhash()
        self.settings = module_or_settings
        if profile is not None:
            module = module_or_settings
            try:
                self.settings = getattr(module, profile)()
            except AttributeError, e:
                if "has no attribute '%s'" % profile not in str(e):
                    raise
                raise ValueError('settings profile "%s" not found in this application' % profile)
        self.ag_setup()
        self.registry_setup()
        self.settings_setup()
        self.filesystem_setup()
        self.logging_setup()
        self.routing_setup()
        self.init_templating()

    def registry_setup(self):
        blazeweb.settings._push_object(self.settings)
        blazeweb.ag._push_object(self.ag)

    def ag_setup(self):
        self.ag = BlankObject()
        self.ag.app = self
        self.ag.view_functions = {}
        self.ag.hierarchy_import_cache = {}
        self.ag.hierarchy_file_cache = {}

    def settings_setup(self):
        # now we need to assign plugin's settings to the main setting object
        for pname in listplugins():
            try:
                Settings = findobj('%s:config.settings.Settings' % pname)
                ms = Settings()
                # update the plugin's settings with any plugin level settings made
                # at the app level.  This allows us to override plugin settings
                # in our application's settings.py file.
                try:
                    ms.update(self.settings.plugins[pname])
                except KeyError, e:
                    if pname not in str(e):
                        raise # pragma: no cover
                self.settings.plugins[pname] = ms
            except HierarchyImportError, e:
                if '%s.config.settings' % pname not in str(e) and 'Settings' not in str(e):
                    raise # pragma: no cover

        # lock the settings, this ensures that an attribute error is thrown if an
        # attribute is accessed that doesn't exist.  Without the lock, a new attr
        # would be created, which is undesirable since any "new" attribute at this
        # point would probably be an accident
        self.settings.lock()

    def filesystem_setup(self):
        # create the writeable directories if they don't exist already
        if self.settings.auto_create_writeable_dirs:
            mkdirs(self.settings.dirs.data)
            mkdirs(self.settings.dirs.logs)
            mkdirs(self.settings.dirs.tmp)
        # copy static files if requested
        if self.settings.auto_copy_static.enabled:
            copy_static_files(self.settings.auto_copy_static.delete_existing)

    def logging_setup(self):
        create_handlers_from_settings(self.settings)

    def routing_setup(self):
        # setup the Map object with the appropriate settings
        self.ag.route_map = Map(**self.settings.routing.map.todict())

        # load view modules so routes from @asview() get setup correctly
        if self.settings.auto_load_views:
            visitmods('views')

        # application routes first since they should take precedence
        self.add_routing_rules(self.settings.routing.routes)

        # now the routes from plugin settings
        for pname in self.settings.plugins.keys():
            psettings = self.settings.plugins[pname]
            try:
                self.add_routing_rules(psettings.routes)
            except AttributeError, e:
                if "no attribute 'routes'" not in str(e):
                    raise  # pragma: no cover

    def init_templating(self):
        engine = default_engine()
        self.ag.tplengine = engine()

    def add_routing_rules(self, rules):
        if self.settings.routing.prefix:
            # prefix the routes with the prefix in the app settings class
            self.ag.route_map.add(Submount(self.settings.routing.prefix, rules ))
        else:
            for rule in rules or ():
                self.ag.route_map.add(rule)

    def request_manager(self, environ):
        return RequestManager(self, environ)

    def response_context(self, error_doc_code):
        return ResponseContext(error_doc_code)

    def response_cycle(self, endpoint, args, error_doc_code=None):
        blazeweb.rg.forward_queue = [(endpoint, args)]
        while True:
            with self.response_context(error_doc_code):
                endpoint, args = blazeweb.rg.forward_queue[-1]
                return self.dispatch_to_endpoint(endpoint, args)

    def dispatch_to_endpoint(self, endpoint, args):
        log.debug('dispatch to %s (%s)', endpoint, args)
        if '.' not in endpoint:
            vklass = findview(endpoint)
        else:
            vklass = _RouteToTemplate
        v = vklass(args, endpoint)
        return v.process()

    def wsgi_app(self, environ, start_response):
        with self.request_manager(environ):
            try:
                try:
                    endpoint, args = blazeweb.rg.urladapter.match()
                except HTTPException, e:
                    log.debug('routing HTTP exception %s from %s', e, blazeweb.rg.request.url)
                    raise
                log.debug('wsgi_app processing %s (%s)', endpoint, args)
                response = self.response_cycle(endpoint, args)
            except Redirect, e:
                response = e.response
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
        endpoint = self.settings.error_docs.get(e.code)
        log.debug('handling http exception %s with %s', e, endpoint)
        if endpoint is None:
            return e
        try:
            return self.response_cycle(endpoint, {}, error_doc_code=e.code)
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
        if not self.settings.exception_handling:
            raise
        if 'email' in self.settings.exception_handling:
            try:
                mail_programmers('exception encountered', exception_with_context())
            except Exception, e:
                log.exception('exception when trying to email exception')
        if 'format' in self.settings.exception_handling:
            response = InternalServerError()
            response.description = '<pre>%s</pre>' % escape(exception_with_context())
            return response
        if 'handle' in self.settings.exception_handling:
            endpoint = self.settings.error_docs.get(500)
            if endpoint is not None:
                log.debug('handling exception with error doc endpoint %s' % endpoint)
                try:
                    return self.response_cycle(endpoint, {}, error_doc_code=500)
                except HTTPException, httpe:
                    log.debug('error doc endpoint %s raised HTTPException: %s', endpoint, httpe)
                except Exception, exc:
                    log.exception('error doc endpoint %s raised exception:', endpoint)
            # turn the exception into a 500 server response
            log.debug('handling exception with generic 500 response')
            return InternalServerError()
        raise

    def __call__(self, environ, start_response):
        return self.wsgi_app(environ, start_response)
