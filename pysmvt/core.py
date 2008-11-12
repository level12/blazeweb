import sys
from os import path
from paste.registry import StackedObjectProxy

__all__ = [
    'ag',
    'app',
    'rg',
    'settings',
    'session',
    'user',
    'redirect',
    'forward',
    '_getview',
    'getview'
]

# a "global" object for storing data and objects (like tcp connections or db
# connections) across requests (application scope)
ag = StackedObjectProxy(name="ag")
# a reference to the main application object
app = StackedObjectProxy(name="app")
# the request "global" object, stores data and objects "globaly" during a request.  The
# environment, urladapter, etc. get saved here. (request only)
rg = StackedObjectProxy(name="rco")
# all of the settings data (application scope)
settings = StackedObjectProxy(name="settings")
# the http session (request only)
session = StackedObjectProxy(name="session")
# the user object (request only)
user = StackedObjectProxy(name="user")

from pysmvt.exceptions import Redirect, ProgrammingError, ForwardException

def redirect(location, permanent=False, code=302 ):
    """
        location: URI to redirect to
        permanent: if True, sets code to 301 HTTP status code
        code: allows 303 or 307 redirects to be sent if needed, see
            http://www.w3.org/Protocols/rfc2616/rfc2616-sec10.html
    """
    if permanent:
        code = 301
    raise Redirect(location, code)

def forward(endpoint, args = {}):
    if len(rg.forward_queue) == 10:
        raise ProgrammingError('forward loop detected: %s' % '->'.join([g[0] for g in rg.forward_queue]))
    rg.forward_queue.append((endpoint, args))
    raise ForwardException

def getview(endpoint, **kwargs):
    return _getview(endpoint, kwargs, 'getview')
    
def _getview(endpoint, args, called_from ):
    """
        called_from options: client, forward, getview, template
    """
    from pysmvt.view import RespondingViewBase
    from pysmvt.utils import module_import, traceback_depth
    
    app_mod_name, vclassname = endpoint.split(':')
    
    try:
        vklass = module_import('%s.views' % app_mod_name, vclassname)
        if called_from in ('client', 'forward', 'error docs'):
            if not issubclass(vklass, RespondingViewBase):
                if called_from == 'client':
                    raise ProgrammingError('Route exists to non-RespondingViewBase view "%s"' % vklass.__name__)
                elif called_from == 'error docs':
                    raise ProgrammingError('Error document handling endpoint used non-RespondingViewBase view "%s"' % vklass.__name__)
                else:
                    raise ProgrammingError('forward to non-RespondingViewBase view "%s"' % vklass.__name__)
    except ImportError, e:
        # we check the stack trace depth to if it is an import
        # error from the view module b/c we want that propogated
        _, _, tb = sys.exc_info()
        # 2 = view class name wasn't found
        # 3 = view module wasn't found
        if traceback_depth(tb) in (3,4):
            msg = 'Could not load view "%s": %s' % (endpoint, str(e))
            ag.logger.debug(msg)
            raise ProgrammingError(msg)
        raise
    
    vmod_dir = path.dirname(sys.modules[vklass.__module__].__file__)
    
    oView = vklass(vmod_dir, endpoint, args )
    return oView()