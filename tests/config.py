from os import path

from pysmvt.application import Application
from pysmvt.config import DefaultSettings, appinit
from pysmvt import settings

from pysutils import prependsitedir
prependsitedir(__file__, 'applications')

basedir = path.dirname(path.abspath(__file__))

class Testruns(DefaultSettings):
    def __init__(self):
        # call parent init to setup default settings
        DefaultSettings.__init__(self, 'pysmvttestapp', basedir)
        
        self.db.uri = 'sqlite:///'
        
        #######################################################################
        # EXCEPTION HANDLING
        #######################################################################
        # if True, most exceptions will be caught and
        # turned into a 500 response, which will optionally be handled by
        # the error docs handler if setup for 500 errors
        #
        #  *** SET TO True FOR PRODUCTION ENVIRONMENTS ***
        self.exceptions.hide = False
        
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
                
        self.emails.from_default = 'root@localhost'
        self.emails.programmers = ['randy@rcs-comp.com']
        self.email.subject_prefix = '[pysvmt test app] '

def make_console(settings_cls=Testruns, **kwargs):
    appinit(settings_cls=settings_cls, **kwargs)
    return Application()

def init_settings(customsettings=None):
    if customsettings:
        settings._push_object(customsettings)
    return settings._push_object(Testruns('testsettings', path.dirname(path.abspath(__file__))))
        

def destroy_settings():
    settings._pop_object()