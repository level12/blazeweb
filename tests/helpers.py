from beaker.middleware import SessionMiddleware
from paste.registry import RegistryManager
from werkzeug.routing import Rule
from pysmvt.application import WSGIApplication
from pysmvt.config import DefaultSettings, appinit
from pysmvt.controller import Controller
from pysmvt.middleware import RequestManager
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
        # disable so they don't interfere with testing
        #self.exceptions.hide = False
        #self.debugger.enabled = False

class TestController(Controller):
    def _execute_view(self, endpoint, args, called_from):
        vklass = endpoint
        return vklass('', vklass.__name__, args)()

class TestWsgiApplication(WSGIApplication):
    def setup_controller(self):
        self.controller = TestController(self.settings)

def create_testapp():
    appinit(settings_cls=TestSettings)
    app = TestWsgiApplication()
    app = RegistryManager(app)
    return app

class AsViewHelper(RespondingViewBase):
    func_mapping = {}
    def default(self, funckey=None):
        return self.func_mapping[funckey]()
        
def asview(f):
    AsViewHelper.func_mapping[f.__name__] = f
    return f

def create_altstack_app(use_session=False):
    class AltApp(TestWsgiApplication):
        def __call__(self, environ, start_response):
            resp = self.controller(environ, start_response)
            if 'beaker.session' in environ:
                environ['beaker.session'].save()
            return resp
    appinit(settings_cls=TestSettings)
    app = AltApp()
    app = RequestManager(app, app.ag, app.settings)
    if use_session:
        app = SessionMiddleware(app, **dict(app.settings.beaker))
    app = RegistryManager(app)
    return app