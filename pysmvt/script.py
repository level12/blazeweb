# -*- coding: utf-8 -*-
import sys
import os
from os import path
from pysmvt import ag, db, settings
import pysmvt.commands
from pysmvt.config import appslist
from pysmvt.utils import tb_depth_in
from werkzeug import script
from paste.util.multidict import MultiDict

class UsageError(Exception):
    pass

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

def main():
    """ this is what our command line `pysmvt` calls to start """
    # this first thing we need to do is look in the args for a -p argument
    # which will tell us our profile.  This is a hack, but I don't know how
    # to get around it at this point.  An application has to be loaded to get
    # all the available actions, but when using initdb, having two applications
    # fails b/c the meta data doesn't get loaded for the second application
    try:
        p_arg = sys.argv.index('-p')
        profile = sys.argv[p_arg+1]
        # remove the argument and value from sys.argv
        sys.argv = sys.argv[:p_arg] + sys.argv[p_arg+2:]
    except ValueError, e:
        if 'list.index' not in str(e):
            raise
        profile = 'Default'
    
    try:
        if _is_application_context():
            # create an application and let everything run inside it's request
            app = make_console(profile)
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