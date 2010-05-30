from os import path

import beaker.session
import werkzeug
from werkzeug import SharedDataMiddleware, DebuggedApplication
from werkzeug.exceptions import HTTPException
from werkzeug import create_environ

from pysmvt import settings, ag, session, rg, user
from pysmvt import routing
from pysmvt.controller import Controller
from pysmvt.users import User
from pysmvt.utils import randhash, Context

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
        
class WSGIApplication(Application):

    def __init__(self):
        Application.__init__(self)
        
        self.setup_controller()
    
    def registry_globals(self, environ):
        if environ.has_key('paste.registry'):
            environ['paste.registry'].register(settings, self.settings)
            environ['paste.registry'].register(ag, self.ag)
            environ['paste.registry'].register(session, environ['beaker.session'])
            environ['paste.registry'].register(user, self.setup_user(environ))
            environ['paste.registry'].register(rg, Context())

    def __call__(self, environ, start_response):
        self.registry_globals(environ)
        return self.controller(environ, start_response)

    def setup_controller(self):
        self.controller = Controller(self.settings)
    
    def setup_user(self, environ):

        try:
            return environ['beaker.session']['__pysmvt_user']
        except KeyError, e:
            if '__pysmvt_user' not in str(e):
                raise
            environ['beaker.session']['__pysmvt_user'] = User()
            # this is for BC, and will eventually be removed
            environ['beaker.session']['user'] = environ['beaker.session']['__pysmvt_user']
            return environ['beaker.session']['__pysmvt_user']
        