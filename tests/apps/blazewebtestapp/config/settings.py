from os import path
from werkzeug.routing import Rule
from blazeweb.config import DefaultSettings

basedir = path.dirname(path.dirname(__file__))
app_package = path.basename(basedir)

class Default(DefaultSettings):
    def init(self):
        self.dirs.base = basedir
        self.app_package = app_package
        DefaultSettings.init(self)

        self.auto_copy_static.enabled = True

        # don't use exception catching, debuggers, logging, etc.
        self.apply_test_settings()

    def get_storage_dir(self):
        return path.join(basedir, '..', '..', 'test-output', app_package)

class Testruns(Default):
    def init(self):
        Default.init(self)

        self.supporting_apps = ['blazewebtestapp2']
        self.setup_plugins()

        self.routing.routes.extend([
            Rule('/', endpoint='tests:Index')
        ])

        self.emails.programmers = ['you@example.com']
        self.email.subject_prefix = '[pysvmt test app] '

        # a fake setting for testing
        self.foo = 'bar'

    def setup_plugins(self):
        self.add_plugin(app_package, 'tests')
        self.add_plugin(app_package, 'nomodel')
        self.add_plugin(app_package, 'nosettings')
        self.add_plugin(app_package, 'sessiontests')
        self.add_plugin(app_package, 'routingtests')
        self.add_plugin(app_package, 'usertests')
        self.add_plugin(app_package, 'disabled')
        self.plugins.blazewebtestapp.disabled.enabled = False
        # blazewebtestapp2 plugins
        self.add_plugin('blazewebtestapp2', 'tests')
        self.add_plugin('blazewebtestapp2', 'routingtests')

class WithLogs(Testruns):
    def init(self):
        # call parent init to setup default settings
        Testruns.init(self)

        self.logs.enabled = True
