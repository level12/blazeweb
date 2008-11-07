from os import path
import sys
from pysmvt.wrappers import Request, Response
from pysmvt.exceptions import RedirectException, ForwardException
from pysmvt.user import SessionUser
from pysmvt import routing
from werkzeug import ClosingIterator, SharedDataMiddleware, MultiDict
from werkzeug.routing import Map, Submount
from werkzeug.exceptions import HTTPException, NotFound, InternalServerError
import werkzeug.utils
from beaker.middleware import SessionMiddleware

from pysmvt.application import request_context as rc
from pysmvt.application import request_context_manager as rcm

from pysmvt.database import get_dbsession, get_dbsession_cls
from pysmvt.utils import randchars, traceback_depth

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
        """Dispatch an incoming request."""
        # set up all the stuff we want to have for this request.  That is
        # creating a request object, propagating the application to the
        # current context and instanciating the database session.
        rc.ident = randchars()
        self.bind_to_context()
        rc.view_queue = []
        request = Request(environ)
        response = None
        
        rc.session = environ['beaker.session']
        self._setup_user()

        # bind the route map to the current environment
        urls = self.urlAdapter = self._route_map.bind_to_environ(environ)

        try:
            # initialize endpoint to avoid UnboundLocalError
            endpoint = None
            
            # find the requested view based on the URL
            endpoint, args = urls.match()
            
            # for the initial view, only URL arguments get sent
            # to the view, GET arguments can be validated and merged in
            # by the view later
            
            self._inner_requests_wrapper(endpoint, args)
            
            # the responding view should have prepared the response
            response = rc.response
            
        except HTTPException, e:
            if endpoint is None:
                rc.application.logger.debug('URL did not match with any Rules')
            response = e
        except RedirectException:
            # it is assumed that rc.response will have been set appropriately
            # with a proper redirect status code and location header
            # before RedirectException is thrown
            response = rc.response
        except Exception, e:
            rc.application.logger.debug('uncaught exception detected in controller: %s' % str(e))
            raise
        finally:
            # save the user session
            rc.session.save()

            # rollback any uncommitted database transactions.  We assume that
            # an explicit commit will be issued and anything leftover was accidental
            get_dbsession().rollback()
            
            # make sure we get a new DB session for the next request
            get_dbsession_cls().remove()
            
            try: 
                # do we have a response?  If not, then there was an exception
                # that prevented the response from being set.  
                if not response and rc.application.settings.controller.hide_exceptions:
                    return InternalServerError()(environ, start_response)
            finally:
                # handle context local cleanup
                rcm.cleanup()
            
        # send response and perform request cleanup
        return response(environ, start_response)
    
    def _inner_requests_wrapper(self, endpoint, args):
        # this loop allows us to handle forwards
        while True:
            rc.response = Response()
            rc.respview = None
            try: 
                # call the view
                self.call_view(endpoint, args)
                break
            except ForwardException:
                endpoint, args = rc.view_queue.pop()
    
    def redirect(self, location, code=302):
        rc.response = werkzeug.utils.redirect(location, code)
        raise RedirectException()
    
    def forward(self, endpoint, args = {}):
        rc.view_queue.append((endpoint, args))
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
                rc.application.loader.appmod_names('%s.settings' % module, 'routes', globals())
                
                # load the routes from the module
                self._add_routing_rules(routes)
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
    
    def call_view(self, endpoint, args ):
        app_mod_name, vclassname = endpoint.split(':')
        
        try:
            vklass = rc.application.loader.appmod_names('%s.views' % app_mod_name, vclassname)
        except ImportError, e:
            # if we find the module_to_load in the exception message,
            # we know the exception was thrown b/c that module
            # could not be loaded.  Otherwise, its probably an import
            # error from the view module and we want that propogated
            _, _, tb = sys.exc_info()
            # 2 = view class name wasn't found
            # 3 = view module wasn't found
            if traceback_depth(tb) in (2,3):
                rc.application.logger.debug('Could not load "%s": %s', endpoint, str(e))
                raise NotFound
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
        
        # handles all of our static documents (CSS, JS, images, etc.)
        self._setup_static_middleware()
        
        # session middleware
        self._setup_session_middleware()
        
        # free the context locals at the end of the request
        self._dispatch = rcm.make_middleware(self._dispatch)
    
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