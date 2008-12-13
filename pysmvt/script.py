import os
import sys
from pysmvt import ag, appimport, db, settings, modimport
from pysmvt.utils.filesystem import mkpyfile
from pysmvt.utils import pprint, tb_depth_in, traceback_depth
from werkzeug import script, Client, BaseResponse

_calling_mod_locals = sys._getframe(1).f_globals

### helper functions
def _make_app(profile='Default'):
    return _calling_mod_locals['make_app'](profile)

def _shell_init_func(profile='Default'):
    """
    Called on shell initialization.  Adds useful stuff to the namespace.
    """
    app = _make_app(profile)
    return {
        'webapp': app
    }

def make_runserver(app_factory, hostname='localhost', port=5000,
                   use_reloader=False, use_debugger=False, use_evalex=True,
                   threaded=False, processes=1, dnslookups=True):
    """Returns an action callback that spawns a new wsgiref server."""
    def action(profile='Default', hostname=('h', hostname), port=('p', port),
               reloader=use_reloader, debugger=use_debugger,
               evalex=use_evalex, threaded=threaded, processes=processes, dnslookups=dnslookups):
        """Start a new development server."""
        from werkzeug.serving import run_simple
        app = app_factory(profile)
        run_simple(hostname, port, app, reloader, debugger, evalex,
                   None, 1, threaded, processes, dnslookups=dnslookups)
    return action

### Werkzeug script functions
action_shell = script.make_shell(_shell_init_func)

### Action Functions
action_runserver = make_runserver(_make_app, use_reloader=True)

def action_testrun(url=('u', '/'), show_body=('b', False), show_headers=('h', False), show_all=('a', False)):
    """
        Loads the application and makes a request.  Useful for debugging
        with print statements
    """
    
    app = _shell_init_func()['webapp']
    
    c = Client(app, BaseResponse)
    
    #custom post
    #url = '/contributors/edit/10'
    #data = 'name_prefix=&name_first=Randy&name_middle=&name_last=Syring&name_suffix=&organization_id=-2&url=&summary=&submit=Submit&contributor-form-submit-flag=submitted'
    #ct = 'application/x-www-form-urlencoded'
    #cl = len(data)
    #resp = c.post(url, data=data, content_type = ct, content_length = cl)
    resp = c.get(url)
    
    if show_headers or show_all:
        print resp.status
        print resp.headers
    
    if show_body or show_all:
        for respstr in resp.response:
            print respstr

def action_createmod(name=('n', '')):
    """ used to create an application module's file structure"""
    app = _shell_init_func()['webapp']
    modules = appimport('modules')
    
    moddir = os.path.dirname(modules.__file__)
    newdir = os.path.join(moddir, name)
    
    dirs = (newdir, os.path.join(newdir, 'templates'), os.path.join(newdir, 'model'))
    for dirpath in dirs:
        if not os.path.exists(dirpath):
            os.mkdir(dirpath)
    for file in ('__init__.py', 'metadata.py', 'orm.py'):
        fpath = os.path.join(newdir, 'model', file)
        if not os.path.exists(fpath):
            mkpyfile(fpath)
    for file in ('__init__.py', 'actions.py', 'forms.py', 'settings.py',
                 'utils.py', 'views.py', 'commands.py'):
        fpath = os.path.join(newdir, file)
        if not os.path.exists(fpath):
            mkpyfile(fpath)

def action_initmod(targetmod=('m', ''), profile=('p', 'Default')):
    """
        used to allow modules to do setup after they are installed.  Will call
        a function init_db in a module's commands.py file.
    """
    app = _shell_init_func(profile)['webapp']

    # add a session to the db if modules inits need it
    db.sess = db.Session()
    
    # call each AM's appmod_dbinit()
    for appmod in settings.modules.keys():
        if targetmod == appmod or targetmod == '':
            try:
                callable = modimport('%s.commands' % appmod, 'init_module')
                callable()
            except ImportError:
                if not tb_depth_in(3):
                    raise

def main():
    """ this is what our command line `pysmvt` calls to start """
    print 'main called'