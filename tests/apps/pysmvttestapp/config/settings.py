from os import path
from werkzeug.routing import Rule
from pysmvt.config import DefaultSettings

basedir = path.dirname(path.dirname(__file__))
appname = path.basename(basedir)

class Default(DefaultSettings):
    def init(self):
        self.dirs.base = basedir
        self.appname = appname
        DefaultSettings.init(self)

class Testruns(Default):
    def init(self):
        Default.init(self)

        self.supporting_apps = ['pysmvttestapp2']
        self.setup_plugins()

        self.routing.routes.extend([
            Rule('/', endpoint='tests:Index')
        ])

        # don't use exception catching, debuggers, logging, etc.
        self.apply_test_settings()

        self.emails.programmers = ['you@example.com']
        self.email.subject_prefix = '[pysvmt test app] '

        # a fake setting for testing
        self.foo = 'bar'

    def setup_plugins(self):
        self.add_plugin(appname, 'tests')
        self.add_plugin(appname, 'nomodel')
        self.add_plugin(appname, 'nosettings')
        self.add_plugin(appname, 'sessiontests')
        self.add_plugin(appname, 'routingtests')
        self.add_plugin(appname, 'usertests')
        self.add_plugin(appname, 'disabled')
        self.plugins.pysmvttestapp.disabled.enabled = False
        # pysmvttestapp2 plugins
        self.add_plugin('pysmvttestapp2', 'tests')
        self.add_plugin('pysmvttestapp2', 'routingtests')

class WithLogs(Testruns):
    def init(self):
        # call parent init to setup default settings
        Testruns.init(self)

        self.logs.enabled = True
