from blazeweb.application import WSGIApp
from blazeweb.middleware import full_wsgi_stack
from .config import settings as settingsmod


def make_wsgi(profile='Default'):
    app = WSGIApp(settingsmod, profile)
    app = full_wsgi_stack(app)
    return app
