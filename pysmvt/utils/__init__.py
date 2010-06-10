import re
import logging
from traceback import format_exc
from formencode.validators import URL
from formencode import Invalid

from pysmvt import rg
from pysmvt.exceptions import Abort
from pysutils.helpers import pformat

log = logging.getLogger(__name__)

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

def abort(outputobj=None, code=200):
    raise Abort(outputobj, code)

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
    retval += '\n\n== ENVIRON ==\n\n%s' % pformat(rg.environ, 4)
    retval += '\n\n== POST ==\n\n%s\n\n' % pformat(werkzeug_multi_dict_conv(rg.request.form), 4)
    return retval
