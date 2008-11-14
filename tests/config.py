from os import path
import rcsutils

# setup the virtual environment so that we can import specific versions
# of system libraries.  The first 
rcsutils.setup_virtual_env('pysmvt-libs-trunk', __file__, '..', '../applications')

import config
from pysmvt.application import Application
from pysmvt.config import DefaultSettings
from pysmvt import settings

basedir = path.dirname(path.abspath(__file__))

class Testruns(DefaultSettings):
    def __init__(self):
        # call parent init to setup default settings
        DefaultSettings.__init__(self, 'pysmvttestapp', basedir)
        
        self.db.uri = 'sqlite:///'
        
        self.logging.levels = []
        
        #######################################################################
        # EXCEPTION HANDLING
        #######################################################################
        # if True, most exceptions will be caught and
        # turned into a 500 response, which will optionally be handled by
        # the error docs handler if setup for 500 errors
        #
        #  *** SET TO True FOR PRODUCTION ENVIRONMENTS ***
        self.exceptions.hide = False
        # if true, an email will be sent using mail_programmers() whenever
        # an exception is encountered
        self.exceptions.email = False
        # if True, will send exception details to the applications debug file
        self.exceptions.log = True
        
        #######################################################################
        # DEBUGGING
        #######################################################################
        # only matters when exceptions.hide = False.  Possible values:
        # 'standard' : shows a formatted stack trace in the browser
        # 'interactive' : like standard, but has an interactive command line
        #
        #          ******* SECURITY ALERT **********
        # setting to 'inactive' would allow ANYONE who has access to the server
        # to run arbitrary code.  ONLY use in an isolated development
        # environment
        self.debugger.enabled = False
        self.debugger.format = 'interactive'
        
        
        self.emails.programmers = ['randy@rcs-comp.com']
        self.email.subject_prefix = '[pysvmt test app] '
        
        # we are done adding variables to this settings object, so lock it
        self.lock()

def makeapp(profile='Default', **kwargs):
    
    config.appinit(settings, profile, **kwargs)
    
    app = Application()
    
    return app

def init_settings(customsettings=None):
    if customsettings:
        settings._push_object(customsettings)
    return settings._push_object(Testruns('testsettings', path.dirname(path.abspath(__file__))))
        

def destroy_settings():
    settings._pop_object()