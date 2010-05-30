import sys
import random
import re
import logging
from pprint import PrettyPrinter
from pysmvt import settings, user, ag, forward, rg, modimport, appimport
from werkzeug import run_wsgi_app, create_environ
from nose.tools import make_decorator
from formencode.validators import URL
from formencode import Invalid
from markdown2 import markdown
from pysmvt.exceptions import Abort
from pysutils import import_split, OrderedProperties, OrderedDict, \
    safe_strftime, randhash, randchars, toset, tolist, traceback_depth, \
    tb_depth_in, simplify_string, reindent

log = logging.getLogger(__name__)

urlslug = simplify_string

def isurl(s, require_tld=True):
    u = URL(add_http=False, require_tld=require_tld)
    try:
        u.to_python(s)
        return True
    except Invalid:
        url_local = re.compile(r'//localhost(:|/)').search(s)
        if url_local is not None:
            return True
        return False

def fatal_error(user_desc = None, dev_desc = None, orig_exception = None):
    # log stuff
    log.info('Fatal error: "%s" -- %s', dev_desc, str(orig_exception))
    
    # set user message
    if user_desc != None:
        user.add_message('error', user_desc)
        
    # forward to fatal error view
    forward(settings.endpoint.sys_error)

def auth_error(user_desc = None, dev_desc = None):
    # log stuff
    if dev_desc != None:
        log.info('Auth error: %s', dev_desc)
    
    # set user message
    if user_desc != None:
        user.add_message('error', user_desc)
        
    # forward to fatal error view
    forward(settings.endpoint.sys_auth_error)

def bad_request_error(dev_desc = None):
    # log stuff
    if dev_desc != None:
        log.info('bad request error: %s', dev_desc)
        
    # forward to fatal error view
    forward(settings.endpoint.bad_request_error)

def pprint( stuff, indent = 4, asstr=False):
    pp = PrettyPrinter(indent=indent)
    if asstr:
        return pp.pformat(stuff)
    pp.pprint(stuff)

class Context(object):
    """
        just a dummy object to hang attributes off of
    """
    pass

def wrapinapp(wsgiapp):
    """Used to make any callable run inside a WSGI application.

    Example use::

        from pysmvt.routing import current_url
        from pysmvt.utils import wrapinapp

        from testproj.applications import make_wsgi
        app = make_wsgi('Test')

        @wrapinapp(app)
        def test_currenturl():
            assert current_url(host_only=True) == 'http://localhost/'
    """
    def decorate(func):
        def newfunc(*arg, **kw):
            def sendtowsgi():
                func(*arg, **kw)
            environ = create_environ('/[[__handle_callable__]]')
            environ['pysmvt.callable'] = sendtowsgi
            run_wsgi_app(wsgiapp, environ)
        newfunc = make_decorator(func)(newfunc)
        return newfunc
    return decorate

def abort(outputobj=None, code=200):
    raise Abort(outputobj, code)

def import_app_str(impstr):
    return _import_str(appimport, impstr)
    
def import_mod_str(impstr):
    return _import_str(modimport, impstr)

def _import_str(impfunc, impstr):
    path, object, attr = import_split(impstr)
    if object:
        if attr:
            return getattr(impfunc(path, object), attr)
        return impfunc(path, object)
    return impfunc(path)

def tb_depth_in(depths):
    """
    looks at the current traceback to see if the depth of the traceback
    matches any number in the depths list.  If a match is found, returns
    True, else False.
    """
    depths = tolist(depths)
    if traceback_depth() in depths:
        return True
    return False

def traceback_depth(tb=None):
    if tb == None:
        _, _, tb = sys.exc_info()
    depth = 0
    while tb.tb_next is not None:
        depth += 1
        tb = tb.tb_next
    return depth

def werkzeug_multi_dict_conv(md):
    '''
        Werzeug Multi-Dicts are either flat or lists, but we want a single value
        if only one value or a list if multiple values
    '''
    retval = {}
    for key, value in md.to_dict(flat=False).iteritems():
        if len(value) == 1:
            retval[key] = value[0]
        else:
            retval[key] = value
    return retval

def gather_objects(modpath):
    """
        This searches all applications and all modules in all 
        applications for `modpath` and if a python module is found
        returns all the objects found in that module.
        
        Search Order: search order is applications lower in the stack
        first (the primary application is always on top of the stack).  
        The application is searched first, then its modules, and then 
        the next application & modules are searched.
        
        For example, if we had the following applications and modules, 
        with app1 being our primary module and app2 being a supporting
        module, and the module activiation order being: foo, bar, baz
        
        app1.modules.foo
        app1.modules.bar
        app2.modules.foo
        app2.modules.baz
        
        and we called gather_objects('tasks.init_db'), then the 
        following python modules would be searched for:
        
        app2.tasks.init_db
        app2.modules.foo.tasks.init_db
        app2.modules.baz.tasks.init_db
        app1.tasks.init_db
        app1.modules.foo.tasks.init_db
        app1.modules.bar.tasks.init_db
        
        and if found, the objects in that module would be added to the
        return value list.
        
        The return value is a list of dictionaries.  Each dictionary in 
        in the list represents the module's symbol table.
    """
    from pysmvt.config import appslist
    retmods = OrderedDict()
    
    def add_to_retmods(modvars):
        modname = modvars['__name__']
        # we don't care about the application, so strip that off
        _, modname = modname.split('.', 1)
        if retmods.has_key(modname):
            retmods[modname]['__override_stack__'].append(retmods[modname]['__name__'])
            retmods[modname].update(modvars)
        else:
            retmods[modname] = {}
            retmods[modname].update(modvars)
            retmods[modname]['__override_stack__'] = []
        # remove builtins for sanity's sake
        del retmods[modname]['__builtins__']
        
    # get commands from all applications (primary and supporting)
    for app_name in appslist(reverse=True):
        try:
            cmd_mod = __import__('%s.%s' % (app_name, modpath), globals(), locals(), [''])
            add_to_retmods(vars(cmd_mod))
        except ImportError:
            if tb_depth_in(0):
                pass
                
        # get commands from all modules in all applications
        for appmod in settings.modules.keys():
                try:
                    cmd_mod = __import__('%s.modules.%s.%s' % (app_name, appmod, modpath), globals(), locals(), [''])
                    add_to_retmods(vars(cmd_mod))
                except ImportError:
                    if not tb_depth_in(0):
                        raise 
    return retmods.values()

def registry_has_object(to_check):
    """
        can be used to check the registry objects (rg, ag, etc.) in a safe way
        to see if they have been registered
    """
    # try/except is a workaround for paste bug:
    # http://trac.pythonpaste.org/pythonpaste/ticket/408
    try:
        return bool(to_check._object_stack())
    except AttributeError, e:
        if "'thread._local' object has no attribute 'objects'" != str(e):
            raise
        return False
    
