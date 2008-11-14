import os
import sys
from pysmvt import ag, appimport
from pysmvt.utils.filesystem import mkblankfile
from pysmvt.utils import pprint
from werkzeug import script

_calling_mod_locals = sys._getframe(1).f_locals

### helper functions
def _make_app():
    return _calling_mod_locals['make_app']()

def _shell_init_func():
    """
    Called on shell initialization.  Adds useful stuff to the namespace.
    """
    app = _make_app()
    return {
        'webapp': app
    }

### Werkzeug script functions
action_runserver = script.make_runserver(_make_app, use_reloader=True)
action_shell = script.make_shell(_shell_init_func)


### Action Functions
def action_testrun(url=('u', '/'), show_body=('b', False), show_headers=('h', False), show_all=('a', False)):
    """
        Loads the application and makes a request.  Useful for debugging
        with print statements
    """
    from webapp.application import WebApp as wzhwApp
    from werkzeug import Client, BaseResponse
    
    c = Client(wzhwApp(), BaseResponse)
    
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

def action_modcreate(name=('n', '')):
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
            mkblankfile(fpath)
    for file in ('__init__.py', 'actions.py', 'forms.py', 'settings.py',
                 'utils.py', 'views.py'):
        fpath = os.path.join(newdir, file)
        if not os.path.exists(fpath):
            mkblankfile(fpath)

def action_dbinit(module=('m', '')):
    """ used to create database objects & structure """
    app = _shell_init_func()['webapp']
    from pysmvt.database import get_metadata, get_engine
    from pysmvt.utils import call_appmod_dbinits
    from sqlitefktg4sa import auto_assign

    metadata = get_metadata()
    metadata.bind = get_engine()

    # create foreign keys for SQLite
    auto_assign(metadata)

    # create the database objects
    metadata.create_all()

    # call each AM's appmod_dbinit()
    call_appmod_dbinits(module)

def action_appmodinit(module=('m', '')):
    """ used to create database objects & structure """
    app = _shell_init_func()['webapp']
    from pysmvt.database import get_metadata
    from pysmvt.utils import call_appmod_inits

    # call each AM's appmod_dbinit()
    call_appmod_inits(module)