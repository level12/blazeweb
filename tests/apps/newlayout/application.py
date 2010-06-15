from blazeweb.application import WSGIApp
from blazeweb.middleware import full_wsgi_stack
import config.settings as settingsmod
from blazeweb.scripting import application_entry

def make_wsgi(profile='Default'):
    app = WSGIApp(settingsmod, profile)
    # wrap our app in middleware and return
    return full_wsgi_stack(app)

def script_entry():
    application_entry(make_wsgi)
    
if __name__ == '__main__':
    script_entry()



