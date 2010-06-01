from beaker.middleware import SessionMiddleware
from paste.registry import RegistryManager
from werkzeug.routing import Rule
from pysmvt.application import full_wsgi_stack, minimal_wsgi_stack, WSGIApplication
from pysmvt import settings
from pysmvt.config import DefaultSettings, appinit
from pysmvt.view import RespondingViewBase

class TestSettings(DefaultSettings):
    def __init__(self):
        # note that we don't really have a physical location for this "app",
        # so it should not be used for any kind of testing which uses file 
        # system locations
        DefaultSettings.__init__(self, 'testapp', '')

        self.routing.routes.extend([
            Rule('/<funckey>', endpoint=AsViewHelper)
        ])
        self.apply_test_settings()
        self.static_files.enabled = False

class TestWsgiApplication(WSGIApplication): 
    def dispatch_to_view(self, endpoint, args, called_from = None):
        vklass = endpoint
        return vklass('', vklass.__name__, args)()

def create_testapp():
    appinit(settings_cls=TestSettings)
    return minimal_wsgi_stack(TestWsgiApplication)

class AsViewHelper(RespondingViewBase):
    func_mapping = {}
    def default(self, funckey=None):
        return self.func_mapping[funckey]()
        
def asview(f):
    AsViewHelper.func_mapping[f.__name__] = f
    return f

def create_altstack_app(use_session=False):
    appinit(settings_cls=TestSettings)
    if not use_session:
        settings.beaker.enabled=False
    return full_wsgi_stack(TestWsgiApplication)