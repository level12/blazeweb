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
