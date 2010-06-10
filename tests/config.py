from os import path

from pysmvt.application import WSGIApp
from pysmvt.config import DefaultSettings
from pysmvt import settings

from pysutils import prependsitedir
prependsitedir(__file__, 'apps')

class Testruns(DefaultSettings):
    def init(self):
        self.dirs.base = path.dirname(__file__)
        self.appname = path.basename(self.dirs.base)
        DefaultSettings.init(self)

        #######################################################################
        # EXCEPTION HANDLING
        #######################################################################
        self.exception_handling = False

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
        self.emails.programmers = ['you@example.com']
        self.email.subject_prefix = '[pysvmt test app] '

    def get_storage_dir(self):
        return path.join(self.dirs.base, 'test-output', self.appname)

def make_wsgi(settings_cls=Testruns, **kwargs):
    return WSGIApp(settings_cls())

def init_settings(customsettings=None):
    if customsettings:
        settings._push_object(customsettings)
    return settings._push_object(Testruns())

def destroy_settings():
    settings._pop_object()
