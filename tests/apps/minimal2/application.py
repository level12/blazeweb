from os import path
from blazeutils import prependsitedir
from blazeweb.application import WSGIApp
from blazeweb.middleware import full_wsgi_stack
import config.settings as settingsmod
from blazeweb.scripting import application_entry

# make sure our base module gets put on the path
try:
    import minimal2
except ImportError:
    prependsitedir(path.dirname(settingsmod.basedir), 'apps')

def make_wsgi(profile='Default', use_session=True):
    app = WSGIApp(settingsmod, profile)
    if not use_session:
        app.settings.beaker.enabled=False
    return full_wsgi_stack(app)

def script_entry():
    application_entry(make_wsgi)

if __name__ == '__main__':
    script_entry()
