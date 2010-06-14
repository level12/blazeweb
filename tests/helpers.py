from os import path

from werkzeug.routing import Rule
from pysmvt.application import WSGIApp
from pysmvt.middleware import full_wsgi_stack, minimal_wsgi_stack
from pysmvt import settings
from pysmvt.config import DefaultSettings

class TestSettings(DefaultSettings):
    def init(self):
        self.dirs.base = path.dirname(__file__)
        self.appname = 'testapp'
        DefaultSettings.init(self)

        self.apply_test_settings()
        self.static_files.enabled = False

    def get_storage_dir(self):
        return path.join(self.dirs.base, 'test-output', self.appname)

def create_testapp():
    app = WSGIApp(TestSettings())
    return minimal_wsgi_stack(app)

def create_altstack_app(use_session=False):
    app = WSGIApp(TestSettings())
    if not use_session:
        app.settings.beaker.enabled=False
    return full_wsgi_stack(app)
