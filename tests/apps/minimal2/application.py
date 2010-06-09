from os import path
from pysutils import prependsitedir
from pysmvt.application import WSGIApplication
from pysmvt.middleware import full_wsgi_stack
import settings as settingsmod
from pysmvt.scripting import application_entry

# make sure our base module gets put on the path
try:
    import minimal2
except ImportError:
    prependsitedir(path.dirname(settingsmod.basedir), 'apps')

def make_wsgi(profile='Default', middleware='minimal'):
    app = WSGIApplication(settingsmod, profile)
    # wrap our app in middleware and return
    return full_wsgi_stack(app)

def script_entry():
    application_entry(make_wsgi)

if __name__ == '__main__':
    script_entry()
