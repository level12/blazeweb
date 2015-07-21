import fnmatch
import re
import logging
from traceback import format_exc

from formencode.validators import URL
from formencode import Invalid
from blazeutils.helpers import pformat
from blazeutils.strings import reindent
from webhelpers.html import escape
import werkzeug

from blazeweb.globals import rg, settings

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

def abort(send):
    """
        An enhanced version of Werkzeug's abort.  `send` is handled differently
        based on what it is:

        int: assumed to be a HTTP status code; not all codes supported by
            default, see the Werkzeug documentation for an explanation.
        string/unicode: will put the string as the body of a response and send
            it.
        callable: assume its a Response object or other WSGI application; wrap
            in proxy HTTPException and raise it;
        anything else: pformat, escape, wrap in <pre> tags, and treat like
            string/unicode above.
    """
    # this is a circular import if done at the module level
    from blazeweb.wrappers import Response

    response_body = reindent("""
    <!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">
    <title>abort() Response</title>
    <h1 style="margin-bottom: 25px">abort() Response</h1>

    %s""".strip(), 0)

    if isinstance(send, int) or hasattr(send, '__call__'):
        response = send
    elif isinstance(send, basestring):
        response = Response(response_body % escape(send))
    else:
        response = Response(response_body % ('<pre>%s</pre>' % escape(pformat(send))))
    werkzeug.abort(response)

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


def exception_context_filter(data):
    filters = settings.exception_context_filters
    retval = {}
    for key in data.keys():
        value = data[key]
        # Does this value match any of the filter patterns?
        if filter(lambda pattern: fnmatch.fnmatch(key, pattern), filters):
            retval[key] = '<removed>'
        else:
            retval[key] = value
    return retval


def exception_with_context():
    """
        formats the last exception as a string and adds context about the
        request.
    """
    post_data = werkzeug_multi_dict_conv(rg.request.form)
    post_data = exception_context_filter(post_data)

    # Remove HTTP_COOKIE from the environment since it may contain sensitive info.  It will get
    # filtered and inserted next.
    environ = rg.environ.copy()
    if 'HTTP_COOKIE' in environ:
        del environ['HTTP_COOKIE']
        environ['blazeweb.cookies'] = exception_context_filter(rg.request.cookies)

    retval = '\n== TRACE ==\n\n%s' % format_exc()
    retval += '\n\n== ENVIRON ==\n\n%s' % pformat(environ, 4)
    retval += '\n\n== POST ==\n\n%s\n\n' % pformat(post_data, 4)
    return retval


class _Redirect(Exception):
    """
        don't use directly, use redirect() instead
    """
    def __init__(self, response):
        self.response = response

def redirect(location, permanent=False, code=302 ):
    """
        location: URI to redirect to
        permanent: if True, sets code to 301 HTTP status code
        code: allows 303 or 307 redirects to be sent if needed, see
            http://www.w3.org/Protocols/rfc2616/rfc2616-sec10.html
    """
    log = logging.getLogger('blazeweb.core:redirect')
    if permanent:
        code = 301
    log.debug('%d redirct to %s' % (code, location))
    raise _Redirect(werkzeug.redirect(location, code))

def sess_regenerate_id():
    """
        Regenerates the beaker session's id

        Needed until this gets put in place:
        https://bitbucket.org/bbangert/beaker/issue/75
    """
    #rg.session.regenerate_id()
    try:
        rg.session.regenerate_id()
    except AttributeError, e:
        if 'regenerate_id' not in str(e):
            raise
        is_new = rg.session.is_new
        la = rg.session.last_accessed
        rg.session._create_id()
        rg.session.is_new = is_new
        rg.session.last_accessed = la
        rg.session.request['set_cookie'] = True
        if hasattr(rg.session, 'namespace'):
            del rg.session.namespace
