from __future__ import with_statement
import __builtin__
import logging

from blazeutils.datastructures import BlankObject
from blazeutils.strings import randchars, randhash
from blinker import Namespace
from werkzeug.exceptions import HTTPException, InternalServerError
from werkzeug import create_environ
from werkzeug.routing import Map, Submount

from blazeweb.globals import ag, rg, settings, user
from blazeweb.events import signal, SettingsConnectHelper, clear_old_beaker_sessions
from blazeweb.exceptions import ProgrammingError
from blazeweb.hierarchy import findobj, HierarchyImportError, \
    listcomponents, visitmods, findview, split_endpoint
from blazeweb.logs import create_handlers_from_settings
from blazeweb.mail import mail_programmers
from blazeweb.templating import default_engine
from blazeweb.users import UserProxy
from blazeweb.utils import exception_with_context, abort, _Redirect
from blazeweb.utils.filesystem import mkdirs, copy_static_files
from blazeweb.views import _RouteToTemplate, _Forward
from blazeweb.wrappers import Request

log = logging.getLogger(__name__)

class RequestManager(object):
    user_proxy_class = UserProxy

    def __init__(self, app, environ):
        self.app = app
        self.environ = environ

    def init_registry(self):
        environ = self.environ
        environ['paste.registry'].register(rg, BlankObject())
        self.init_rg()
        user_instance = self.init_user()
        environ['paste.registry'].register(user, user_instance)

    def init_rg(self):
        rg.ident = randchars()
        rg.environ = self.environ
        # the request object binds itself to rg.request
        Request(self.environ)
        if self.environ.has_key('beaker.session'):
            rg.session = self.environ['beaker.session']
            log.debug('using beaker sessions')
        else:
            rg.session = None
        # if set, it will be called with an unhandled exception if necessary
        rg.exception_handler = None

    def init_routing(self):
        rg.urladapter = ag.route_map.bind_to_environ(self.environ)

    def init_user(self):
        return self.user_proxy_class()

    def __enter__(self):
        self.init_registry()
        self.init_routing()
        # allow middleware higher in the stack to help initilize the request
        # after the registry variables have been setup
        if 'blazeweb.request_setup' in self.environ:
            for callable in self.environ['blazeweb.request_setup']:
                callable()

    def __exit__(self, exc_type, exc_value, tb):
        # make the user class available to the testing framework if applicable
        # http://pythonpaste.org/webtest/#framework-hooks
        if 'paste.testing' in self.environ:
            u = user._current_obj()
            if isinstance(u, UserProxy):
                # we don't want to send the UserProxy outside of the request
                # because we will get a StackedObjectProxy error when trying
                # to access it.  Better to just send None, b/c an attribute
                # error on None is easier to understand in testing than
                # a proxy registry error
                self.environ['paste.testing_variables']['user'] = None
            else:
                self.environ['paste.testing_variables']['user'] = u
            self.environ['paste.testing_variables']['session'] = rg.session

        if 'blazeweb.request_teardown' in self.environ:
            for callable in self.environ['blazeweb.request_teardown']:
                callable()

class ResponseContext(object):
    def __init__(self, error_doc_code):
        self.environ = rg.environ
        # this gets set if this response context is initilized b/c
        # an error document handler is being called.  It allows the View
        # that handles the error code to know what code it is being called
        # for.
        self.error_doc_code = error_doc_code

    def __enter__(self):
        log.debug('enter response context')
        rg.respctx = self
        # allow middleware higher in the stack to help initilize the response
        if 'blazeweb.response_cycle_setup' in self.environ:
            for callable in self.environ['blazeweb.response_cycle_setup']:
                callable()

    def __exit__(self, exc_type, e, tb):
        log.debug('exit response context started')
        if 'blazeweb.response_cycle_teardown' in self.environ:
            for callable in self.environ['blazeweb.response_cycle_teardown']:
                callable()
        if isinstance(e, _Forward):
            log.debug('forwarding to %s (%s)', e.forward_endpoint, e.forward_args)
            rg.forward_queue.append((e.forward_endpoint, e.forward_args))
            if len(rg.forward_queue) == 10:
                raise ProgrammingError('forward loop detected: %s' % '->'.join([g[0] for g in rg.forward_queue]))
            return True
        if 'beaker.session' in self.environ:
            bs = self.environ['beaker.session']
            if bs.accessed():
                log.debug('saving beaker session, id: %s', bs.id)
                bs.save()
            else:
                log.debug('beaker session not accessed, not saving')
        log.debug('exit response context finished')

class WSGIApp(object):

    def __init__(self, module_or_settings, profile=None):
        self._id = randhash()

        self.init_ag()
        self.init_settings(module_or_settings, profile)
        self.init_signals()
        self.init_events()
        self.init_component_settings()
        self.init_auto_actions()
        self.init_logging()
        self.init_routing()
        self.init_templating()

    def init_settings(self, module_or_settings, profile):
        self.settings = module_or_settings
        # get the settings class and instantiate it
        if profile is not None:
            module = module_or_settings
            try:
                self.settings = getattr(module, profile)()
            except AttributeError, e:
                if "has no attribute '%s'" % profile not in str(e):
                    raise
                raise ValueError('settings profile "%s" not found in this application' % profile)
        SettingsClass = self.settings.__class__
        # look for any attributes on the settings class instance that have
        # been decorated by @settings_connect and connect() them
        for aname, aobj in vars(SettingsClass).iteritems():
            #print aname
            if isinstance(aobj, SettingsConnectHelper):
                aobj.connect()
        settings._push_object(self.settings)

    def init_ag(self):
        self.ag = BlankObject()
        self.ag.app = self
        self.ag.view_functions = {}
        self.ag.hierarchy_import_cache = {}
        self.ag.hierarchy_file_cache = {}
        self.ag.events_namespace = Namespace()
        ag._push_object(self.ag)

    def init_signals(self):
        # signals are weakly referenced, so we need to keep a reference as long
        # as this application is instantiated
        self.signals = (
            signal('blazeweb.pre_test_init'),
            signal('blazeweb.events.initialized'),
            signal('blazeweb.settings.initialized'),
            signal('blazeweb.auto_actions.initialized'),
            signal('blazeweb.logging.initialized'),
            signal('blazeweb.routing.initialized'),
            signal('blazeweb.templating.initialized'),
            signal('blazeweb.request.started'),
            signal('blazeweb.response_cycle.started'),
            signal('blazeweb.response_cycle.ended'),
            signal('blazeweb.request.ended'),
        )

    def init_events(self):
        visitmods('events')
        signal('blazeweb.events.initialized').send(self.init_events)

    def init_component_settings(self):
        # now we need to assign component's settings to the main setting object
        for cname in listcomponents():
            try:
                Settings = findobj('%s:config.settings.Settings' % cname)
                ps = Settings(self.settings)

                # update component-level settings
                try:
                    self.settings.components[cname].setdefaults(ps.for_me)
                except KeyError, e:
                    if cname not in str(e):
                        raise
                    # the application's settings did not override any of this
                    # component's settings and therefore doesn't have a settings
                    # object for this component.  Therefore, we just add it.
                    self.settings.components[cname] = ps.for_me

                # update application-level settings
                self.settings.setdefaults(ps.for_app)
            except HierarchyImportError, e:
                # this happens if the component did not have a settings module or
                # did not have a Settings class in the module
                if '%s.config.settings' % cname not in str(e) and 'Settings' not in str(e):
                    raise # pragma: no cover

        # lock the settings, this ensures that an attribute error is thrown if an
        # attribute is accessed that doesn't exist.  Without the lock, a new attr
        # would be created, which is undesirable since any "new" attribute at this
        # point would probably be an accident
        self.settings.lock()

    def init_auto_actions(self):
        # create the writeable directories if they don't exist already
        if self.settings.auto_create_writeable_dirs:
            mkdirs(self.settings.dirs.data)
            mkdirs(self.settings.dirs.logs)
            mkdirs(self.settings.dirs.tmp)
        # copy static files if requested
        if self.settings.auto_copy_static.enabled:
            copy_static_files(self.settings.auto_copy_static.delete_existing)
        if self.settings.auto_abort_as_builtin == True:
            __builtin__.dabort = abort

        signal('blazeweb.auto_actions.initialized').connect(clear_old_beaker_sessions)
        signal('blazeweb.auto_actions.initialized').send(self.init_auto_actions)

    def init_logging(self):
        create_handlers_from_settings(self.settings)
        signal('blazeweb.logging.initialized').send(self.init_logging)

    def init_routing(self):
        # setup the Map object with the appropriate settings
        self.ag.route_map = Map(**self.settings.routing.map.todict())

        # load view modules so routes from @asview() get setup correctly
        if self.settings.auto_load_views:
            visitmods('views')

        # application routes first since they should take precedence
        self.add_routing_rules(self.settings.routing.routes)

        # now the routes from component settings
        for pname in self.settings.components.keys():
            psettings = self.settings.components[pname]
            try:
                self.add_routing_rules(psettings.routes)
            except AttributeError, e:
                if "no attribute 'routes'" not in str(e):
                    raise  # pragma: no cover

    def init_templating(self):
        engine = default_engine()
        self.ag.tplengine = engine()

    def add_routing_rules(self, rules):
        for rule in rules or ():
            self.ag.route_map.add(rule)

    def request_manager(self, environ):
        return RequestManager(self, environ)

    def response_context(self, error_doc_code):
        return ResponseContext(error_doc_code)

    def response_cycle(self, endpoint, args, error_doc_code=None):
        rg.forward_queue = [(endpoint, args)]
        while True:
            with self.response_context(error_doc_code):
                endpoint, args = rg.forward_queue[-1]
                signal('blazeweb.response_cycle.started').send(endpoint=endpoint, urlargs=args)
                response = self.dispatch_to_endpoint(endpoint, args)
                signal('blazeweb.response_cycle.ended').send(response=response)
                return response

    def dispatch_to_endpoint(self, endpoint, args):
        log.debug('dispatch to %s (%s)', endpoint, args)
        if '.' not in endpoint:
            vklass = findview(endpoint)
        else:
            vklass = _RouteToTemplate
        v = vklass(args, endpoint)
        response = v.process()
        return response

    def wsgi_app(self, environ, start_response):
        log.debug('request received for URL: %s', environ['PATH_INFO'])
        with self.request_manager(environ):
            signal('blazeweb.request.started').send()
            try:
                try:
                    endpoint, args = rg.urladapter.match()
                except HTTPException, e:
                    log.debug('routing HTTP exception %s from %s', e, rg.request.url)
                    raise
                log.debug('wsgi_app processing %s (%s)', endpoint, args)
                response = self.response_cycle(endpoint, args)
            except _Redirect, e:
                response = e.response
            except HTTPException, e:
                if not self.settings.http_exception_handling:
                    raise
                response = self.handle_http_exception(e)
            except Exception, e:
                response = self.handle_exception(e)
            # todo: I wonder if this signal send should be called even in the
            # case of an exception by putting in a finally block
            signal('blazeweb.request.ended').send(response=response)
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
        occours that is not caught.  In debug mode the exception will
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
            if rg.exception_handler:
                return rg.exception_handler(e)
            else:
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
