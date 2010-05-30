# -*- coding: utf-8 -*-
import os
from os import path
from werkzeug.serving import run_simple
from werkzeug import Client, BaseResponse
from werkzeug.script import make_shell
from pysmvt.paster_tpl import run_template
from pysmvt import ag, settings
from pysmvt.script import console_dispatch, make_wsgi, make_console, \
    broadcast_actions
from pysmvt.tasks import run_tasks
from pysutils import pprint

def action_serve(profile='Default', hostname=('h', 'localhost'), port=('p', 5000),
               reloader=True, debugger=False, evalex=False, 
               threaded=False, processes=1):
    """ serve the application by starting a development http server """
    run_simple(hostname, port, make_wsgi(profile), reloader, debugger, evalex,
               None, 1, threaded, processes)

@console_dispatch
def action_shell(ipython=True):
    """
        Start an interactive python shell.
    """
    # set what will already be in the namespace for the shell.  Saves us from
    # typing common import statements.  Not sure what should go here yet.
    shell_namespace = {
    }
    shell_act = make_shell(lambda: shell_namespace, 'pysmvt Interactive Shell')
    shell_act(ipython)

def action_project(projname='', template=('t', 'pysmvt'),
        interactive=True, verbose=False, overwrite=True):
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
        interactive=True, verbose=False, overwrite=True):
    """ creates a new module file structure """
    if not modname:
        print 'Error: `modname` is required'
        return
    output_dir = path.join(settings.dirs.base, 'modules', modname)
    vars = {'modname':modname}
    run_template(interactive, verbose, overwrite, vars,
                 output_dir, template, 'pysmvt_module_template')

@console_dispatch
def action_broadcast(action_to_call=('a', '')):
    """
        calls all instances of broadcast_<action_to_call> in all applications
        and modules
    """
    manual_broadcast(action_to_call)
    
def manual_broadcast(action_to_call):
    if ',' in action_to_call:
        actions_to_call = action_to_call.split(',')
    else:
        actions_to_call = [action_to_call]
    show_action_to_call = len(actions_to_call) > 1 or False
    for action_to_call in actions_to_call:
        if show_action_to_call:
            print '-------------- action to call: %s -----------------' % action_to_call
        if not action_to_call:
            print 'Error: `action` is required'
            return
        for key, callable in broadcast_actions.iteritems():
            if key == action_to_call:
                print 'calling: %s' % callable.__name__
                callable()

def action_testrun(url=('u', '/'), profile='Default', show_body=('b', False), show_headers=('h', False), show_all=('a', False)):
    """
        Loads the application and makes a request.  Useful for debugging
        with print statements
    """
    app = make_wsgi(profile)
    
    c = Client(app, BaseResponse)
    resp = c.get(url)

    if show_headers or show_all:
        print resp.status
        print resp.headers
    
    if show_body or show_all:
        for respstr in resp.response:
            print respstr

@console_dispatch
def action_routes(endpoints=False):
    """ prints out all routes in the mapper """
    toprint = []
    for rule in ag.route_map.iter_rules():
        if endpoints:
            toprint.append((rule.rule, rule.endpoint))
        else:
            toprint.append(rule.rule)
    pprint(toprint)

@console_dispatch
def action_tasks(tasks_to_run='', test_only=('t', False)):
    """ run task(s) (csv for multiple)"""
    tasks = tasks_to_run.split(',')
    run_tasks(tasks, test_only=test_only)
