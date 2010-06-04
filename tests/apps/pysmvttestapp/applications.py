from pysmvt import config
from pysmvt.application import Application, full_wsgi_stack
import settings as settingsmod

def make_wsgi(profile='Default', **kwargs):
    config.appinit(settingsmod, profile, **kwargs)
    return full_wsgi_stack()

def make_console(profile='Default', **kwargs):
    config.appinit(settingsmod, profile, **kwargs)
    return Application()