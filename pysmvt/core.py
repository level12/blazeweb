import sys
from os import path
import logging
from paste.registry import StackedObjectProxy

log = logging.getLogger(__name__)

__all__ = [
    'ag',
    'rg',
    'settings',
    'session',
    'user',
    'redirect',
    'forward',
    '_getview',
    'getview',
    'db',
]

# a "global" object for storing data and objects (like tcp connections or db
# connections) across requests (application scope)
ag = StackedObjectProxy(name="ag")
# the request "global" object, stores data and objects "globaly" during a request.  The
# environment, urladapter, etc. get saved here. (request only)
rg = StackedObjectProxy(name="rg")
# all of the settings data (application scope)
settings = StackedObjectProxy(name="settings")
# the http session (request only)
session = StackedObjectProxy(name="session")
# the user object (request only)
user = StackedObjectProxy(name="user")
# the db object (application scope)
db = StackedObjectProxy(name="db")

from pysmvt.exceptions import Redirect, ProgrammingError, ForwardException

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
    raise Redirect(location, code)

def forward(endpoint, args = {}):
    raise ForwardException(endpoint, args)

def getview(endpoint, **kwargs):
    return _getview(endpoint, kwargs, 'getview')

def _getview(endpoint, args, called_from ):
    """
        called_from options: client, forward, getview, template
    """
    from pysmvt.view import RespondingViewBase
    from pysmvt.utils import tb_depth_in

    app_mod_name, vclassname = endpoint.split(':')

    try:
        vklass = modimport('%s.views' % app_mod_name, vclassname, False)
        if called_from in ('client', 'forward', 'error docs'):
            if not issubclass(vklass, RespondingViewBase):
                if called_from == 'client':
                    raise ProgrammingError('Route exists to non-RespondingViewBase view "%s"' % vklass.__name__)
                elif called_from == 'error docs':
                    raise ProgrammingError('Error document handling endpoint used non-RespondingViewBase view "%s"' % vklass.__name__)
                else:
                    raise ProgrammingError('forward to non-RespondingViewBase view "%s"' % vklass.__name__)
    except ImportError, e:
        # traceback depth of 3 indicates we can't find the module or we can't
        # find the class in a module
        if tb_depth_in(3):
            msg = 'Could not load view "%s": %s' % (endpoint, str(e))
            log.info(msg)
            raise ProgrammingError(msg)
        raise

    vmod_dir = path.dirname(sys.modules[vklass.__module__].__file__)

    oView = vklass(vmod_dir, endpoint, args )
    return oView()
