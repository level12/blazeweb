from os import path
from blazeweb.globals import rg
from blazeweb.application import WSGIApp
from blazeweb.config import DefaultSettings
from blazeweb.middleware import minimal_wsgi_stack
from blazeweb.views import asview
from blazeweb.wrappers import Response

class Settings(DefaultSettings):
    def init(self):
        self.dirs.base = path.dirname(__file__)
        self.app_package = path.basename(self.dirs.base)
        DefaultSettings.init(self)
        self.auto_load_views = True
        
        # don't use exception catching, debuggers, logging, etc.
        self.apply_test_settings()

    def get_storage_dir(self):
        return path.join(self.dirs.base, '..', '..', 'test-output', self.app_package)

settings = Settings()

app = WSGIApp(settings)
wsgiapp = minimal_wsgi_stack(app)
