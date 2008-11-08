from os import path
import logging
from werkzeug import LocalManager, Local

# Setup some local objects that will ensure a thread safe per-request
# environment for "global" variables.  I.e. they are objcts that allow us to
# have "global" variables per request
# rcontext = 
request_context = rc = Local()
request_context_manager = LocalManager([request_context])

from pysmvt.controller import Controller
from pysmvt.utils import Loader, Logger, randhash
from pysmvt.database import load_models

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

    def __init__(self, settings, profile = 'default'):
        rc.application = self
        
        self._id = randhash()
        
        # a custom importer
        self.setup_loader()
        
        # which settings profile do we use
        self.profile = profile
        
        #calculate the web applications static directory
        self.staticDir = path.join(self.baseDir, 'static')
        
        # load settings class from the settings module
        self.settings = getattr(settings, self.profile.capitalize())()
        
        # application logging object      
        self.setup_logger()
        
        self.setup_controller()
        
        # make sure the DB model is loaded
        self.load_db_model()

    def bind_to_context(self):
        """
        Useful for the shell.  Binds the application to the current active
        context.  It's automatically called by the shell command.
        """
        rc.application = self
    
    def __call__(self, environ, start_response):
        self.bind_to_context()
        """Just forward a WSGI call to the first internal middleware."""
        return self.controller(environ, start_response)
    
    def setup_controller(self):
        self.controller = Controller()
    
    def setup_logger(self):
        logger_prefix = '%s.%s' % (self.__class__.__name__, self._id)
        
        formatter = logging.Formatter("%(asctime)s - %(request_ident)s - " \
           "%(message)s")
        
        # debug logger to put debug logs in one file
        dlogger = logging.getLogger('%s.debug' % logger_prefix)
        dlogger.setLevel(logging.DEBUG)
        fhd = logging.FileHandler(path.join(self.settings.dirs.logs, 'debug.log'))
        #fhd.setLevel(logging.DEBUG)
        fhd.setFormatter(formatter)
        dlogger.addHandler(fhd)
        
        # info logger to put info logs in another file
        ilogger = logging.getLogger('%s.info' % logger_prefix)
        ilogger.setLevel(logging.INFO)
        fhi = logging.FileHandler(path.join(self.settings.dirs.logs, 'info.log'))
        #fhi.setLevel(logging.INFO)
        fhi.setFormatter(formatter)
        ilogger.addHandler(fhi)
        
        # application logger to put application logs in another file
        alogger = logging.getLogger('%s.application' % logger_prefix)
        alogger.setLevel(9)
        fha = logging.FileHandler(path.join(self.settings.dirs.logs, 'application.log'))
        #fhi.setLevel(logging.INFO)
        fha.setFormatter(formatter)
        alogger.addHandler(fha)
        
        self.logger = Logger(dlogger, ilogger, alogger)
    
    def setup_loader(self):
        self.loader = Loader()
    
    def load_db_model(self):
        load_models()