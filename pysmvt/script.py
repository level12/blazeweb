# -*- coding: utf-8 -*-
import os
import sys
from os import path
from pysmvt import ag, appimport, db, settings, modimport
import pysmvt.commands
from pysmvt.config import appslist
from pysmvt.utils.filesystem import mkpyfile
from pysmvt.utils import pprint, tb_depth_in, traceback_depth
from werkzeug import script, Client, BaseResponse
from paste.util.multidict import MultiDict

class UsageError(Exception):
    pass

### helper functions
def _make_app(profile='Default'):
    return _calling_mod_locals['make_app'](profile)

def prep_app(profile):
    if not _is_application_context():
        raise UsageError('this command must be run from inside an '
                         'application\'s directory')
    app_name = _app_name()
    return __import__('%s.applications' % app_name, globals(), locals(), ['make_wsgi', 'make_console'])

def make_wsgi(profile):
    appmod = prep_app(profile)
    return appmod.make_wsgi(profile)
    
def make_console(profile):
    appmod = prep_app(profile)
    return appmod.make_console(profile)

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
    try:
        if _is_application_context():
            # create an application and let everything run inside it's request
            app = make_console('Default')
            app.start_request()
            _werkzeug_run()
            app.end_request()
        else:
            _werkzeug_run()
    except UsageError, e:
        print 'Error: %s' % e

def _werkzeug_run():
    script.run(_gather_actions())

def _gather_actions():
    """
        Ssearches all applications and application modules for available actions.
        Searches from least signifcant to most signifcant so that the more
        significant actions get precidence.
    """
    actions = MultiDict()
    # we will always gather actions from the pysmvt commands module
    actions.update(vars(pysmvt.commands))
    if _is_application_context():
        # get commands from all applications (primary and supporting)
        for app_name in appslist(reverse=True):
            try:
                cmd_mod = __import__('%s.commands' % app_name, globals(), locals(), [''])
                actions.update(vars(cmd_mod))
            except ImportError:
                if tb_depth_in(0):
                    pass
                    
            # get commands from all modules in all applications
            for appmod in settings.modules.keys():
                    try:
                        cmd_mod = __import__('%s.modules.%s.commands' % (app_name, appmod), globals(), locals(), [''])
                        actions.update(vars(cmd_mod))
                    except ImportError:
                        if not tb_depth_in(0):
                            raise
        ag.command_actions = actions
    return actions

def _is_application_context():
    """
        See if we can find a pysmvt application that we can instantiate if we
        need to.  This will determine our "context".
    """
    app_name = _app_name()
    if app_name:
        # once we know the app name, we can try and import the Default
        # settings
        #settings_mod = __import__('%s.settings' % app_name, globals(), locals(), ['Default'])
        return True
    else:
        return False

def _app_name():
    cwd = os.getcwd()
    # every application has to have a settings.py file, see if it is in the cwd
    settings_path = path.join(cwd, 'settings.py')
    if path.exists(settings_path):
        app_path = path.dirname(settings_path)
        app_name = path.basename(app_path)
        return app_name
    return None