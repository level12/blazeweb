# -*- coding: utf-8 -*-
import os
from os import path
from werkzeug.serving import run_simple
from werkzeug import Client, BaseResponse
from pysmvt.paster_tpl import run_template
from pysmvt import ag

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
    run_template(interactive, verbose, overwrite, vars,
                 output_dir, template, 'pysmvt_project_template')

def action_module(modname='', template=('t', 'pysmvt'),
        interactive=True, verbose=True, overwrite=True):
    """ creates a new module file structure """
    if not modname:
        print 'Error: `modname` is required'
        return

def action_broadcast(action=''):
    """ calls all instances of broadcast_* actions in all applications and modules """
    if not action:
        print 'Error: `action` is required'
        return
    for key, callable in ag.command_actions.iteritems():
        if key.startswith('broadcast_%s' % action):
            callable()

def action_testrun(url=('u', '/'), profile='Default', show_body=('b', False), show_headers=('h', False), show_all=('a', False)):
    """
        Loads the application and makes a request.  Useful for debugging
        with print statements
    """
    from pysmvt.script import make_wsgi
    app = make_wsgi(profile)
    
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