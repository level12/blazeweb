from os import path
import sys
from traceback import format_exc

from werkzeug.routing import Map, Submount, RequestRedirect
from werkzeug.exceptions import HTTPException, NotFound, InternalServerError, \
    MethodNotAllowed
import werkzeug.utils

from pysmvt import settings, session, user, rg, ag, getview, _getview, modimport
from pysmvt.exceptions import ForwardException, ProgrammingError, Redirect
from pysmvt.mail import mail_programmers
from pysmvt.utils import randchars, traceback_depth, log_info, log_debug, pprint
from pysmvt.wrappers import Request, Response

# Note: this controller is only instantiated per-process, not per request.
# Therefore, anything that needs to be initialized per application/per process
# can go in __init__, but anything that needs to be initialized per request
# needs to go in dispatch_request()
class Controller(object):
    """
    The controller is responsible for handling the request and responding
    appropriately
    """

    def __init__(self, settings):
        
        self.settings = settings
        
        # Routing Map
        self._route_map = Map()
        
        # load routes from the application and settings files
        self._init_routes()

    def dispatch_request(self, environ, start_response):
        
        self._wsgi_request_setup(environ)

        try:
            response = self._error_documents_handler(environ)
            self._wsgi_request_cleanup()
            return response(environ, start_response)
        finally:
            pass
    
    def _wsgi_request_setup(self, environ):
        # WSGI request setup
        rg.ident = randchars()
        rg.environ = environ
        # the request object binds itself to rg.request
        request = Request(environ)
        
    def _wsgi_request_cleanup(self):
        # save the user session
        session.save()
    
    def _response_cleanup(self):
        # if we do a forward, this would still be set, so we need to
        # unset it
        try: 
            del rg.respview
        except AttributeError:
            pass
        
        # until we get the forward system outside the controller,
        # we should rollback any changes not comitted to avoid
        # unexpected bleed over when doing forwards
        if rg.environ.get('sqlalchemy.sess', None):
            # sqlalchemy sometimes throws errors here with sqlite about
            # connections being shared across threads.  We also
            # get problems with the connection no longer existing
            try:
                rg.environ['sqlalchemy.sess'].rollback()
            except:
                pass
    
    def _error_documents_handler(self, environ):
        response = orig_resp = self._exception_handling('client', environ)
        def get_status_code(response):
            if isinstance(response, HTTPException):
                return response.code
            else:
                return response.status_code
        code = get_status_code(response)
        if code in settings.error_docs:
            handling_endpoint = settings.error_docs.get(code)
            ag.logger.info('error docs: handling code %d with %s' % (code, handling_endpoint))
            environ['pysmvt.controller.error_docs_handler.response'] = response
            new_response = self._exception_handling('error docs', endpoint=handling_endpoint)
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
                ag.logger.debug('error docs: encountered non-200 status code response '
                        '(%d) when trying to handle with %s' % (get_status_code(new_response), handling_endpoint))
        if isinstance(response, HTTPException) and not isinstance(response, Redirect):
            messages = user.get_messages()
            if messages:
                msg_html = ['<h2>Error Details:</h2><ul>']
                for msg in messages:
                    msg_html.append('<li>(%s) %s</li>' % (msg.severity, msg.text))
                msg_html.append('</ul>')
                response.description = response.description + '\n'.join(msg_html)
        return response
    
    def _exception_handling(self, called_from, environ = None, endpoint=None, args = {}):
        try:
            if environ:
                endpoint, args = self._endpoint_args_from_env(environ)
            response = self._inner_requests_wrapper(endpoint, args, called_from)
        except HTTPException, e:
            ag.logger.info('exception handling caught HTTPException "%s", sending as response' % e.__class__.__name__)
            response = e
        except Exception, e:
            if settings.exceptions.log:
                ag.logger.debug('exception handling: %s' % str(e))
            if settings.exceptions.email:
                trace = format_exc()
                envstr = pprint(rg.environ, 4, True)
                mail_programmers('exception encountered', '== TRACE ==\n\n%s\n\n== ENVIRON ==\n\n%s' % (trace, envstr))
            if settings.exceptions.hide:
                # turn the exception into a 500 server response
                response = InternalServerError()
            else:
                raise
        return response
    
    def _endpoint_args_from_env(self, environ):
        try:
            # bind the route map to the current environment
            urls = rg.urladapter = self._route_map.bind_to_environ(environ)
            
            # initialize endpoint to avoid UnboundLocalError
            endpoint = None
            
            # find the requested view based on the URL
            return urls.match()
        
        except (NotFound, MethodNotAllowed, RequestRedirect):
            if endpoint is None:
                ag.logger.info('URL (%s) generated HTTPException' % environ['PATH_INFO'])
            raise
        
    def _inner_requests_wrapper(self, endpoint, args, called_from):
        # this loop allows us to handle forwards
        rg.forward_queue = [(endpoint, args)]
        while True:
            try: 
                # call the view
                endpoint, args = rg.forward_queue[-1]
                response = _getview(endpoint, args, called_from)
                if not isinstance(response, Response):
                    raise ProgrammingError('view %s did not return a response object' % endpoint)
                return response
            except ForwardException:
                called_from = 'forward'
            finally:
                self._response_cleanup()
    
    def __call__(self, environ, start_response):
        """Just forward a WSGI call to the first internal middleware."""
        return self.dispatch_request(environ, start_response)
    
    def _init_routes(self):
        """ add routes to the main Map object from the application settings and
            from module settings """
       
        # application routes
        self._add_routing_rules(self.settings.routing.routes)
       
        # module routes        
        for module in self.settings.modules.keys():
            try:
                Settings = modimport('%s.settings' % module, 'Settings')
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
                    e.args = '%s (from %s.settings.py)' % (str(e), module), 
                    raise
    
    def _add_routing_rules(self, rules):
        if self.settings.routing.prefix:
            # prefix the routes with the prefix in the app settings class
            self._route_map.add(Submount( self.settings.routing.prefix, rules ))
        else:
            for rule in rules or ():
                self._route_map.add(rule)

    

