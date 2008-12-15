# -*- coding: utf-8 -*-
import os
from os import path
from werkzeug.serving import run_simple
from pysmvt.paster_tpl import ProjectTemplate, dummy_cmd
#
#def make_runserver(app_factory, hostname=, port=5000,
#                   use_reloader=False, use_debugger=False, use_evalex=True,
#                   threaded=False, processes=1, dnslookups=True):
#    """Returns an action callback that spawns a new wsgiref server."""
#    
#    return action
#
#@wsgi(profile_by='position')
def action_serve(profile='Default', hostname=('h', 'localhost'), port=('p', 5000),
               reloader=True, debugger=False, evalex=False, 
               threaded=False, processes=1):
    """ serve the application by starting a development http server """
    from pysmvt.script import make_wsgi
    run_simple(hostname, port, make_wsgi(profile), reloader, debugger, evalex,
               None, 1, threaded, processes)

#@console
#def action_shell(_app=None):
#    return script.make_shell(lambda: {'webapp':_app})
#
#@console
#def action_module(modname='', template=('t', 'mod_default'), _app=None ):
#    """ creates a new application module file structure """
#    pass
#
# this action doesn't need an application context to function
def action_project(projname='', template=('t', 'pysmvt'),
        interactive=True, verbose=True, overwrite=True):
    """ creates a new project file structure """
    if not projname:
        print 'Error: `projname` is required'
        return
    output_dir = path.join(os.getcwd(), '%s-dist' % projname)
    vars = {'project': projname,
            'package': projname,
        }
    cmd = dummy_cmd(interactive, verbose, overwrite)
    pt = ProjectTemplate('pysmvt')
    #pt = BasicPackage('basic')
    pt.check_vars(vars, cmd)
    pt.run(cmd, output_dir, vars)

#@console
#def action_broadcast(action='', _app=None ):
#    """ calls all instances of action in all applications and modules """
#    pass