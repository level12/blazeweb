import sys
import random
from pprint import PrettyPrinter
from pysmvt.application import request_context as rc
from pysmvt.application import request_context_manager as rcm
from werkzeug.debug.tbtools import get_current_traceback
from formencode.validators import URL
from formencode import Invalid
from markdown2 import markdown

def reindent(s, numspaces):
    """ reinidents a string (s) by the given number of spaces (numspaces) """
    leading_space = numspaces * ' '
    lines = [ leading_space + line.strip()
                for line in s.splitlines()]
    return '\n'.join(lines)

def urlslug(s, length=None):
    import re
    #$slug = str_replace("&", "and", $string);
    # only keep alphanumeric characters, underscores, dashes, and spaces
    s = re.compile( r'[^\/a-zA-Z0-9_ \\-]').sub('', s)
    # replace forward slash, back slash, underscores, and spaces with dashes
    s = re.compile(r'[\/ \\_]+').sub('-', s)
    # make it lowercase
    s = s.lower()
    if length is not None:
        return s[:length-1].rstrip('-')
    else:
        return s

def isurl(s):
    u = URL(add_http=False)
    try:
        u.to_python(s)
        return True
    except Invalid:
        return False

class Loader(object):
    """
        gets references to python modules in the application.  Used instead of
        `import` because application modules have to be application agnostic
    """
    
    def __init__(self):
        # will save module references
        self.module_refs = {}
    
    def _load_module(self, dotted_location):
        """
            get a reference to a module and save in the application
            
            dotted_location = dotted location for something on Python Path
        """
        try:
            cMod = self.module_refs[dotted_location]
        except KeyError:
            # The last [''] is very important!
            cMod = __import__(dotted_location, globals(), locals(), [''])
            self.module_refs[dotted_location] = cMod
        return cMod
    
    def appmod_names(self, from_dotted_loc, to_import=None, scope = None):
        """ locate a python module (.py) in an Application Module """       
        return self.app_names('modules.%s' % from_dotted_loc, to_import, scope)
    
    def app_names(self, from_dotted_loc, to_import=None, scope = None):
        """ get one or more objects from a python module (.py) in our main app
            or one of our supporting apps """
        retval = []
        to_import = tolist(to_import)
        module = self.app_module(from_dotted_loc)
        if len(to_import) == 0:
            return module
        for name_to_import in to_import:
            if hasattr(module, name_to_import):
                retval.append(getattr(module, name_to_import))
                if scope is not None:
                    scope[name_to_import] = getattr(module, name_to_import)
            else:
                raise ImportError('cannot import name %s' % name_to_import)
        if len(retval) > 1:
            return retval
        if len(retval) == 1:
            return retval.pop()
        return
    
    def app_module(self, dotted_loc):
        """ import a python module (.py) from dotted_loc in our main app or
            one of our supporting apps """
        apps_to_try = [rc.application.appPackage] + rc.application.settings.supporting_apps
        for app in apps_to_try:
            try:
                module_to_load = '%s.%s' % (app, dotted_loc)        
                return self._load_module(module_to_load)
            except ImportError, e:
                # if the import error wasn't for what we loaded, then
                # there was in import error in the module we tried to import
                # re-raise that exception
                _, _, tb = sys.exc_info()
                #print 'except: %d %s %s ' % (traceback_depth(tb), str(e), module_to_load)
                if traceback_depth(tb) > 1:
                    raise
        raise ImportError('cannot import module %s' % dotted_loc)
    
    def app(self, appname):
        return self._load_module(appname)

def module_import(dotted_mod_name, from_list=None ):
    calling_locals = sys._getframe(1).f_locals
    rc.application.loader.appmod_names(dotted_mod_name, from_list, calling_locals)

def app_import(dotted_app_name, from_list=None ):
    calling_locals = sys._getframe(1).f_locals
    rc.application.loader.app_names(dotted_app_name, from_list, calling_locals)

def traceback_depth(tb):
    depth = 0
    while tb.tb_next is not None:
        depth += 1
        tb = tb.tb_next
    return depth

def fatal_error(user_desc = None, dev_desc = None, orig_exception = None):
    # log stuff
    rc.application.logger.debug('Fatal error: "%s" -- %s', dev_desc, str(orig_exception))
    
    # set user message
    if user_desc != None:
        rc.user.add_message('error', user_desc)
        
    # forward to fatal error view
    rc.controller.forward(rc.application.settings.endpoint.sys_error)

def auth_error(user_desc = None, dev_desc = None):
    # log stuff
    if dev_desc != None:
        rc.application.logger.debug('Auth error: %s', dev_desc)
    
    # set user message
    if user_desc != None:
        rc.user.add_message('error', user_desc)
        
    # forward to fatal error view
    rc.controller.forward(rc.application.settings.endpoint.sys_auth_error)

def bad_request_error(dev_desc = None):
    # log stuff
    if dev_desc != None:
        rc.application.logger.debug('bad request error: %s', dev_desc)
        
    # forward to fatal error view
    rc.controller.forward(rc.application.settings.endpoint.bad_request_error)

# from sqlalchemy
def tolist(x, default=[]):
    if x is None:
        return default
    if not isinstance(x, (list, tuple)):
        return [x]
    else:
        return x
    
def toset(x):
    if x is None:
        return set()
    if not isinstance(x, set):
        return set(tolist(x))
    else:
        return x

def pprint( stuff, indent = 4):
    pp = PrettyPrinter(indent=indent)
    pp.pprint(stuff)

def call_appmod_dbinits(singlemod=None):
    for module in rc.application.settings.modules.keys():
        if singlemod == module or singlemod == '':
            try:
                callables = rc.application.loader.appmod_names('%s.settings' % module, 'appmod_dbinits')
                for tocall in tolist(callables):
                    tocall()
            except ImportError:
                pass
        
def call_appmod_inits(module):
    """ call the initilization methods on an AM """
    if not module:
        raise ValueError('"module" parameter must not be empty')
    try:
        callables = rc.application.loader.appmod_names('%s.settings' % module, 'appmod_inits')
        for tocall in tolist(callables):
                tocall()
    except ImportError, e:
        # check the exception depth to make sure the import
        # error we caught was a missing settings.appmod_inits
        _, _, tb = sys.exc_info()
        if traceback_depth(tb) == 2:
            pass
        else:
            raise
        
def log_info(msg):
    rc.application.logger.info(msg)

def log_debug(msg):
    rc.application.logger.debug(msg)

def log_application(msg):
    rc.application.logger.application(msg)
    
class Logger(object):
    def __init__(self, dlogger, ilogger, alogger):
        self.dlogger = dlogger
        self.ilogger = ilogger
        self.alogger = alogger
    
    def debug(self, msg, *args, **kwargs):
        if 'debug' in rc.application.settings.logging.levels:
            d = {'request_ident':rc.ident}
            kwargs['extra'] = d
            self.dlogger.debug(msg, *args, **kwargs)
    
    def info(self, msg):
        if 'info' in rc.application.settings.logging.levels:
            d = {'request_ident':rc.ident}
            self.ilogger.info(msg, extra = d)
    
    def application(self, msg):
        d = {'request_ident':rc.ident}
        self.alogger.log(9, msg, extra = d)
        
def randchars(n = 12):
    charlist = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    return ''.join(random.choice(charlist) for _ in range(n))

def safe_strftime(value, format='%m/%d/%Y %H:%I', on_none=''):
    if value is None:
        return on_none
    return value.strftime(format)

class OrderedProperties(object):
    """An object that maintains the order in which attributes are set upon it.

    Also provides an iterator and a very basic getitem/setitem
    interface to those attributes.

    (Not really a dict, since it iterates over values, not keys.  Not really
    a list, either, since each value must have a key associated; hence there is
    no append or extend.)
    """

    def __init__(self, initialize=True):
        self._data = OrderedDict()
        self._initialized=initialize
        
    def __len__(self):
        return len(self._data)

    def __iter__(self):
        return self._data.itervalues()

    def __add__(self, other):
        return list(self) + list(other)

    def __setitem__(self, key, object):
        self._data[key] = object

    def __getitem__(self, key):
        return self._data[key]

    def __delitem__(self, key):
        del self._data[key]

    def __setattr__(self, item, value):
        # this test allows attributes to be set in the __init__ method
        if self.__dict__.has_key('_initialized') == False or self.__dict__['_initialized'] == False:
            self.__dict__[item] = value
        # any normal attributes are handled normally when they already exist
        # this would happen if they are given different values after initilization
        elif self.__dict__.has_key(item):       
            self.__dict__[item] = value
        # attributes added after initialization are stored in _data
        else:
            self._data[item] = value


    def __getstate__(self):
        return {'_data': self.__dict__['_data']}

    def __setstate__(self, state):
        self.__dict__['_data'] = state['_data']

    def __getattr__(self, key):
        try:
            return self._data[key]
        except KeyError:
            raise AttributeError(key)

    def __contains__(self, key):
        return key in self._data

    def update(self, value):
        self._data.update(value)

    def get(self, key, default=None):
        if key in self:
            return self[key]
        else:
            return default

    def keys(self):
        return self._data.keys()

    def has_key(self, key):
        return self._data.has_key(key)

    def clear(self):
        self._data.clear()


class OrderedDict(dict):
    """A dict that returns keys/values/items in the order they were added."""

    def __init__(self, ____sequence=None, **kwargs):
        self._list = []
        if ____sequence is None:
            if kwargs:
                self.update(**kwargs)
        else:
            self.update(____sequence, **kwargs)

    def clear(self):
        self._list = []
        dict.clear(self)

    def sort(self, fn=None):
        self._list.sort(fn)

    def update(self, ____sequence=None, **kwargs):
        if ____sequence is not None:
            if hasattr(____sequence, 'keys'):
                for key in ____sequence.keys():
                    self.__setitem__(key, ____sequence[key])
            else:
                for key, value in ____sequence:
                    self[key] = value
        if kwargs:
            self.update(kwargs)

    def setdefault(self, key, value):
        if key not in self:
            self.__setitem__(key, value)
            return value
        else:
            return self.__getitem__(key)

    def __iter__(self):
        return iter(self._list)

    def values(self):
        return [self[key] for key in self._list]

    def itervalues(self):
        return iter(self.values())

    def keys(self):
        return list(self._list)

    def iterkeys(self):
        return iter(self.keys())

    def items(self):
        return [(key, self[key]) for key in self.keys()]

    def iteritems(self):
        return iter(self.items())

    def __setitem__(self, key, object):
        if key not in self:
            self._list.append(key)
        dict.__setitem__(self, key, object)

    def __delitem__(self, key):
        dict.__delitem__(self, key)
        self._list.remove(key)

    def pop(self, key, *default):
        present = key in self
        value = dict.pop(self, key, *default)
        if present:
            self._list.remove(key)
        return value

    def popitem(self):
        item = dict.popitem(self)
        self._list.remove(item[0])
        return item

class QuickSettings(OrderedProperties):
    def __init__(self, initialize=True):
        self._locked = False
        OrderedProperties.__init__(self, initialize)
    
    def lock(self):
        self._locked = True
        for child in self._data.values():
            if isinstance(child, QuickSettings):
                child.lock()
    
    def __getattr__(self, key):
        if not self._data.has_key(key):
            if not self._locked:
                self._data[key] = QuickSettings()
            else:
                raise AttributeError('attribute %s not found (object is locked)' % key)
        return self._data[key]
    

