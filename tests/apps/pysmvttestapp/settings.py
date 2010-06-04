from os import path
from werkzeug.routing import Rule
from pysmvt.config import DefaultSettings

class Default(DefaultSettings):
    def init(self):
        self.dirs.base = path.dirname(__file__)
        self.appname = path.basename(self.dirs.base)
        DefaultSettings.init(self)
        
class Testruns(Default):
    def init(self):
        Default.init(self)
        
        self.supporting_apps = ['pysmvttestapp2']
        
        self.modules.tests.enabled = True
        self.modules.nomodel.enabled = True
        self.modules.nosettings.enabled = True
        self.modules.sessiontests.enabled = True
        self.modules.usertests.enabled = True
        self.modules.routingtests.enabled = True
        self.modules.disabled.enabled = False
        
        self.routing.routes.extend([
            Rule('/', endpoint='tests:Index')
        ])
        
        # don't use exception catching, debuggers, logging, etc.
        self.apply_test_settings()        
        
        self.emails.programmers = ['you@example.com']
        self.email.subject_prefix = '[pysvmt test app] '
        
        # a fake setting for testing
        self.foo = 'bar'

class WithLogs(Testruns):
    def init(self):
        # call parent init to setup default settings
        Testruns.init(self)
        
        self.logs.enabled = True

        