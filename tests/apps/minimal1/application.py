from os import path
from pysmvt import rg
from pysmvt.application import WSGIApp
from pysmvt.config import DefaultSettings
from pysmvt.middleware import minimal_wsgi_stack
from pysmvt.views import asview
from pysmvt.wrappers import Response

class Settings(DefaultSettings):
    def init(self):
        self.dirs.base = path.dirname(__file__)
        self.app_package = path.basename(self.dirs.base)
        DefaultSettings.init(self)
        self.auto_load_views = True

    def get_storage_dir(self):
        return path.join(self.dirs.base, '..', '..', 'test-output', self.app_package)

settings = Settings()

app = WSGIApp(settings)
wsgiapp = minimal_wsgi_stack(app)
