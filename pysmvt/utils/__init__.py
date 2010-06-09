import sys
import random
import re
import logging
from traceback import format_exc
from pprint import PrettyPrinter
from pysmvt import settings, user, ag, forward, rg
from werkzeug import run_wsgi_app, create_environ
from nose.tools import make_decorator
from formencode.validators import URL
from formencode import Invalid
from markdown2 import markdown
from pysmvt.exceptions import Abort
from pysutils import import_split, OrderedProperties, OrderedDict, \
    safe_strftime, randhash, randchars, toset, tolist, simplify_string, reindent

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

def exception_with_context():
    """
        formats the last exception as a string and adds context about the
        request.
    """
    retval = '\n== TRACE ==\n\n%s' % format_exc()
    retval += '\n\n== ENVIRON ==\n\n%s' % pprint(rg.environ, 4, True)
    retval += '\n\n== POST ==\n\n%s\n\n' % pprint(werkzeug_multi_dict_conv(rg.request.form), 4, True)
    return retval
