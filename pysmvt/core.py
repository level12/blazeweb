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
    'modimport',
    'appimport',
    'modimportauto',
    'appimportauto',
    'db',
    'appfilepath'
]

# a "global" object for storing data and objects (like tcp connections or db
# connections) across requests (application scope)
ag = StackedObjectProxy(name="ag")
# the request "global" object, stores data and objects "globaly" during a request.  The
# environment, urladapter, etc. get saved here. (request only)
rg = StackedObjectProxy(name="rco")
# all of the settings data (application scope)
settings = StackedObjectProxy(name="settings")
# the http session (request only)
session = StackedObjectProxy(name="session")
# the user object (request only)
user = StackedObjectProxy(name="user")
# the db object (application scope)
db = StackedObjectProxy(name="db")

from pysmvt.exceptions import Redirect, ProgrammingError, ForwardException

def modimportauto(dotted_loc, from_list=None):
    """
        like `modimport`, but grabs the caller's globals and inserts
        modules or objects into it, just like native `import`
    """
    globals = sys._getframe(1).f_globals
    modimport(dotted_loc, from_list, globals)

def modimport(dotted_loc, from_list=None, globals = None ):
    """
        like `appimport`, but at the module instead of the app level.
        
        ex. modimport('tests.model.orm') == appimport('modules.tests.model.orm')
    """
    return appimport('modules.%s' % dotted_loc, from_list, globals)
    
def appimportauto(from_dotted_loc, from_list=None ):
    """
        like `appimport`, but grabs the caller's globals and inserts
        modules or objects into it, just like native `import`
    """
    globals = sys._getframe(1).f_globals
    appimport(from_dotted_loc, from_list, globals)

def appimport(from_dotted_loc, from_list=None, globals = None ):
    """
        get one or more objects from a python module (.py) in our main app
        or one of our supporting apps
        
        from_dotted_loc: python dotted import path, minus the application
        
            appimportauto('utils') == import myapp.utils
        
        but if myapp.utils doesn't exist, might be this:
        
            appimportauto('utils') == import supportingapp.utils
        
        if you have a supporting app setup in settings.supporting_apps
        
        from_list: is a string or list of attributes to import from
        `from_dotted_loc`:
        
            appimportauto('utils', 'helperfunc') == from myapp.utils import helperfunc
            
        globals: the callers globals().  If sent, imported modules and attributes
        will be imported into caller's namespace.
        
        return value: module object, attribute object, or list of attribute objects
        depending on `from_list`:
            appimport('utils') == <module 'utils'>
            appimport('utils', 'helperfunc') == <func 'helperfunc'>
            appimport('utils', ['a', 'b']) == [<func 'a'>, <func 'b'>]
    """
    from pysmvt.utils import tolist
    
    retval = []
    to_import = tolist(from_list)
    if len(to_import) == 0:
        module = _import(from_dotted_loc)
        if globals:
            # we just want the name after the last dot
            objname = module.__name__.split('.')[-1]
            globals[objname] = module
        return module
    for name_to_import in to_import:
        module = _import(from_dotted_loc, name_to_import)
        retval.append(getattr(module, name_to_import))
        if globals:
            globals[name_to_import] = getattr(module, name_to_import)
    if len(retval) == 1:
        return retval[0]
    return retval

def _import(dotted_location, attr=None):
    """
        import a python module (.py) in our main app or
        one of our supporting apps
        
        dotted_location = dotted location of python module to import without
            top level application reference.  example:
            
                __import__('myapp.settings', fromlist=['']) == _import('settings')
            
            the advantage is that you don't have to know the application's
            module name (which is required for Application Modules since they
            need to work cross-app) but also that you can get a reference
            to a supporting apps python modules as well (i.e. inheritance, kind
            of).  So, if myapp.settings didn't exist, but supportapp.settings
            did, then you would get:
            
                _import('settings') == supportapp.settings
                
    """
    from pysmvt.utils import traceback_depth
    
    # the first time this function is used for this applicaiton, we need to
    # do some setup
    if not hasattr(ag, '_import_cache'):
        ag._import_cache = dict()
    
    if attr:
        cachekey = '%s:%s' % (dotted_location, attr)
        if ag._import_cache.get(cachekey):
            return __import__(ag._import_cache.get(cachekey), globals(), locals(), [attr])
    else:
        cachekey = dotted_location
        if ag._import_cache.get(dotted_location):
            return __import__(ag._import_cache.get(dotted_location), globals(), locals(), [''])

    # if the module's location wasn't cached, or the module at that location
    # doesn't have the requested attribute, we need to search for the module
    apps_to_try = [settings.appname] + settings.supporting_apps
    for app in apps_to_try:
        try:
            pymodtoload = '%s.%s' % (app, dotted_location)
            found = __import__(pymodtoload, globals(), locals(), [''])
            if attr is None or hasattr(found, attr):
                ag._import_cache[cachekey] = pymodtoload
                return found
        except ImportError:
            if traceback_depth() > 0:
                raise
    if attr:
        raise ImportError('cannot import "%s" with attribute "%s" from any application' % (dotted_location, attr))
    else:
        raise ImportError('cannot import "%s" from any application' % dotted_location)

def appfilepath(*args):
    """
        return the full path to the directory of `ppath` which is looked up
        in a hierarchial fashion.  This allows us to "inherit" files from
        supporting apps.
        
        example:
        
        appfilepath('myfile.txt')
        
        returns '/projects/myapp' if '/projects/myapp/myfile.txt' exists
        returns '/projects/supportingapp' if '/projects/myapp/myfile.txt' does
        not exist but '/projects/supportingapp/myfile.txt' exists
    """
    from pysmvt.config import appslist
    from pysmvt.utils import tolist
    
    # the first time this function is used for this applicaiton, we need to
    # do some setup
    if not hasattr(ag, '_file_lookup_cache'):
        ag._file_lookup_cache = dict()
    
    ppaths = args
    
    for ppath in ppaths:
        ppath = path.normpath(ppath)
        if ag._file_lookup_cache.has_key(ppath):
            return ag._file_lookup_cache[ppath]
        
        for app in appslist():
            app_dir = path.dirname(__import__(app).__file__)
            fpath = path.join(app_dir, ppath)
            if path.exists(fpath):
                ag._file_lookup_cache[ppath] = fpath
                return fpath
    
    raise ProgrammingError('could not locate "%s" in any application' % ppath)
        

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
