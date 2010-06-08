from pysmvt.application import Application, WSGIApplication
from pysmvt.middleware import full_wsgi_stack
import config.settings as settingsmod

def make_wsgi(profile='Default'):
    app = WSGIApplication(settingsmod, profile)
    app = full_wsgi_stack(app)
    return app

def make_console(profile='Default'):
    return Application(settingsmod, profile)
