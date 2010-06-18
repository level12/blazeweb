import sys
from os import path
import logging

from paste.registry import StackedObjectProxy
import werkzeug

log = logging.getLogger(__name__)

__all__ = [
    'ag',
    'rg',
    'settings',
    'user',
    'redirect',
    'forward',
]

# a "global" object for storing data and objects (like tcp connections or db
# connections) across requests (application scope)
ag = StackedObjectProxy(name="ag")
# the request "global" object, stores data and objects "globaly" during a request.  The
# environment, urladapter, etc. get saved here. (request only)
rg = StackedObjectProxy(name="rg")
# all of the settings data (application scope)
settings = StackedObjectProxy(name="settings")
# the user object (request only)
user = StackedObjectProxy(name="user")

from pysmvt.exceptions import Redirect, Forward

def redirect(location, permanent=False, code=302 ):
    """
        location: URI to redirect to
        permanent: if True, sets code to 301 HTTP status code
        code: allows 303 or 307 redirects to be sent if needed, see
            http://www.w3.org/Protocols/rfc2616/rfc2616-sec10.html
    """
    log = logging.getLogger('pysmvt.core:redirect')
    if permanent:
        code = 301
    log.debug('%d redirct to %s' % (code, location))
    raise Redirect(werkzeug.redirect(location, code))

def forward(endpoint, **kwargs):
    raise Forward(endpoint, kwargs)
