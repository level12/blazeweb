from os import path

from werkzeug.routing import Rule
from pysmvt.application import WSGIApplication
from pysmvt.middleware import full_wsgi_stack, minimal_wsgi_stack
from pysmvt import settings
from pysmvt.config import DefaultSettings
from pysmvt.view import RespondingViewBase

class TestSettings(DefaultSettings):
    def init(self):
        self.dirs.base = path.dirname(__file__)
        self.appname = 'testapp'
        DefaultSettings.init(self)

        self.routing.routes.extend([
            Rule('/<funckey>', endpoint=AsViewHelper)
        ])
        self.apply_test_settings()
        self.static_files.enabled = False

    def get_storage_dir(self):
        return path.join(self.dirs.base, 'test-output', self.appname)

class TestWsgiApplication(WSGIApplication):
    def dispatch_to_view(self, endpoint, args, called_from = None):
        vklass = endpoint
        return vklass('', vklass.__name__, args)()

def create_testapp():
    app = TestWsgiApplication(TestSettings())
    return minimal_wsgi_stack(app)

class AsViewHelper(RespondingViewBase):
    func_mapping = {}
    def default(self, funckey=None):
        return self.func_mapping[funckey]()

def asview(f):
    AsViewHelper.func_mapping[f.__name__] = f
    return f

def create_altstack_app(use_session=False):
    app = TestWsgiApplication(TestSettings())
    if not use_session:
        app.settings.beaker.enabled=False
    return full_wsgi_stack(app)
