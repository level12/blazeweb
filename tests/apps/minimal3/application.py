from blazeweb.application import WSGIApp
from blazeweb.middleware import minimal_wsgi_stack
import minimal3.settings as settingsmod
app = WSGIApp(settingsmod, 'Settings')
wsgiapp = minimal_wsgi_stack(app)
