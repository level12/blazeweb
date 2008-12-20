# -*- coding: utf-8 -*-
import sys
import os
from os import path
import inspect
from pysmvt import ag, db, settings
from pysmvt.config import appslist, appinit
from pysmvt.utils import tb_depth_in
from werkzeug import script
from paste.util.multidict import MultiDict
from decorator import FunctionMaker

class UsageError(Exception):
    pass

def prep_app():
    if not _is_application_context():
        raise UsageError('this command must be run from inside an '
                         'application\'s directory')
    app_name = _app_name()
    return __import__('%s.applications' % app_name, globals(), locals(), ['make_wsgi', 'make_console'])

def make_wsgi(profile):
    appmod = prep_app()
    return appmod.make_wsgi(profile)
    
def make_console(profile):
    appmod = prep_app()
    return appmod.make_console(profile)

def _get_settings_mod():
    if not _is_application_context():
        raise UsageError('this command must be run from inside an '
                         'application\'s directory')
    app_name = _app_name()
    return __import__('%s.settings' % app_name, globals(), locals(), [''])

def main():
    """ this is what our command line `pysmvt` calls to start """
    # there has to be a 'Default' settings profile
    profile = 'Default'
    try:
        if _is_application_context():
            # we have to at least appinit() with this application's settings
            smod = _get_settings_mod()
            appinit(smod, profile)
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
    import pysmvt.commands
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
    if _app_name():
        return True
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

def _profile_last(caller, func=None):
    """ decorate a decorator so that an additional 'profile' parameter is
        added to the arg spec to be used by the decorator but not passed to
        the decorated function.
    """
    if func is None: # returns a decorator
        fun = FunctionMaker(caller)
        first_arg = inspect.getargspec(caller)[0][0]
        src = 'def %s(%s): return _call_(caller, %s)' % (
            caller.__name__, first_arg, first_arg)
        return fun.make(src, dict(caller=caller, _call_=_profile_last),
                        undecorated=caller)
    else: # returns a decorated function
        fun = FunctionMaker(func)
        src = """def %(name)s(%(signature)s, profile):
    return _call_(_func_, %(signature)s, profile)"""
        ret_func = fun.make(src, dict(_func_=func, _call_=caller), undecorated=func)
        # add the default value for our 'profile' argument
        ret_func.func_defaults = ret_func.func_defaults + ('Default',)
        return ret_func

@_profile_last
def console_dispatch(f, *args):
    """
    A function intended to be a decorator for command actions that need to be
    run in the application context.  The decorated function will be passed
    to the application's console_dispatch method.  It will also preserve the
    original function's signature (to satisfy werkzeug.script's inspection) while
    adding an additional "profile" parameter as the last argument.  This profile
    argument is used by `console_context` to determine which settings profile
    should be instantiated.
    """
    # Because of the way werkzeug script works, all function arguments are
    # always passed by position and defaults are always given.  Therefore,
    # we know that our profile will be in the last position.  We use pop
    # because we need to remove that extra argument before we pass it to
    # f()
    largs = list(args)
    profile = largs.pop()
    def dispatch_wrapper():
        f(*largs)
    app = make_console(profile)
    app.console_dispatch(dispatch_wrapper)
    