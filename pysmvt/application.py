from os import path
import logging

import beaker.session
import werkzeug
from werkzeug import SharedDataMiddleware, DebuggedApplication
from werkzeug.exceptions import HTTPException

from pysmvt import settings, ag, session, rg, user
from pysmvt import routing
from pysmvt.controller import Controller
from pysmvt.database import load_models
from pysmvt.users import SessionUser
from pysmvt.utils import Logger, randhash, Context

# The main web application inherits this.
#
# Note: this application is only instantiated per-process, not per request.
# Therefore, anything that needs to be initialized per application/per process
# can go in __init__, but anything that needs to be initialized per request
# needs to go in dispatch_request()
class Application(object):
    """
    Our central WSGI application.
    """

    def __init__(self):
        self._id = randhash()
    
        # keep local copies of these objects around for later
        # when we need to bind them to the request
        self.settings = settings._current_obj()
        self.ag = ag._current_obj()

        # application logging object      
        self.setup_logger()
        
        self.setup_controller()
        
        # make sure the DB model is loaded
        self.load_db_model()
    
    def __del__(self):
        #settings._pop_object(self.settings)
        #ag._pop_object(self.ag)
        pass
    
    def bind_request_globals(self, environ):
        sesobj = beaker.session.Session(environ)
        session._push_object(sesobj)
        user._push_object(self.setup_user())
        rg._push_object(Context())
    
    def release_request_globals(self):
        session._pop_object()
        user._pop_object()
        rg._pop_object()
    
    def __call__(self, environ, start_response):
        return self.dispatch(environ, start_response)
    
    def dispatch(self, environ, start_response):
        self.registry_globals(environ)
        return self.controller(environ, start_response)
    
    def registry_globals(self, environ):
        if environ.has_key('paste.registry'):
            environ['paste.registry'].register(settings, self.settings)
            environ['paste.registry'].register(ag, self.ag)
            environ['paste.registry'].register(session, environ['beaker.session'])
            environ['paste.registry'].register(user, self.setup_user())
            environ['paste.registry'].register(rg, Context())
    
    def startrequest(self, url='/'):
        """
            will fake a WSGI request with the given relative `url`
            and initialize the controller up to the point where a view
            would normally be called.  This is useful for testing purposes
            as well console applications.  `endrequest()` should be called
            when finished to properly cleanup the request.
        """
        environ = werkzeug.utils.create_environ(url)
        self.bind_request_globals(environ)
        self.controller._wsgi_request_setup(environ)
        try:
            # we don't really care if the route doesn't exist, we just want to make
            # sure the urladapter gets setup correctly so our url_for() based
            # functions work
            self.controller._endpoint_args_from_env(environ)
        except HTTPException:
            pass
    
    def endrequest(self):
        """
            compliments startrequest() and should only be used as a compliment
            for that function.
        """
        self.controller._response_cleanup()
        self.controller._wsgi_request_cleanup()
        self.release_request_globals()
        
    def setup_logger(self):
        logger_prefix = '%s.%s' % (self.__class__.__name__, self._id)
        
        formatter = logging.Formatter("%(asctime)s - %(request_ident)s - " \
           "%(message)s")
        
        loggers = []
        if 'debug' in settings.logging.levels:
            # debug logger to put debug logs in one file
            dlogger = logging.getLogger('%s.debug' % logger_prefix)
            dlogger.setLevel(logging.DEBUG)
            fhd = logging.FileHandler(path.join(settings.dirs.logs, 'debug.log'))
            #fhd.setLevel(logging.DEBUG)
            fhd.setFormatter(formatter)
            dlogger.addHandler(fhd)
            loggers.append(dlogger)
        else:
            loggers.append(None)
        
        if 'info' in settings.logging.levels:
            # info logger to put info logs in another file
            ilogger = logging.getLogger('%s.info' % logger_prefix)
            ilogger.setLevel(logging.INFO)
            fhi = logging.FileHandler(path.join(settings.dirs.logs, 'info.log'))
            #fhi.setLevel(logging.INFO)
            fhi.setFormatter(formatter)
            ilogger.addHandler(fhi)
            loggers.append(ilogger)
        else:
            loggers.append(None)
        
        if 'appliction' in settings.logging.levels:
            # application logger to put application logs in another file
            alogger = logging.getLogger('%s.application' % logger_prefix)
            alogger.setLevel(9)
            fha = logging.FileHandler(path.join(settings.dirs.logs, 'application.log'))
            #fhi.setLevel(logging.INFO)
            fha.setFormatter(formatter)
            alogger.addHandler(fha)
            loggers.append(alogger)
        else:
            loggers.append(None)
        
        #if loggers:
        ag.logger = Logger(*loggers)
    
    def load_db_model(self):
        load_models()
        
    def setup_controller(self):
        self.controller = Controller(self.settings)
    
    def setup_user(self):
        return SessionUser()