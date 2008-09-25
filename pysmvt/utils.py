import sys
import random
from pprint import PrettyPrinter
from pysmvt.application import request_context as rc
from pysmvt.application import request_context_manager as rcm
from werkzeug.debug.tbtools import get_current_traceback

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
    
    def appmod_names(self, from_dotted_loc, to_import, scope = None):
        """ locate a python module (.py) in an Application Module """       
        return self.app_names('modules.%s' % from_dotted_loc, to_import, scope)
    
    def app_names(self, from_dotted_loc, to_import, scope = None):
        """ get one or more objects from a python module (.py) in our main app
            or one of our supporting apps """
        retval = []
        to_import = tolist(to_import)
        module = self.app_module(from_dotted_loc)
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
    rc.controller.forward(rc.application.settings.sys_error_endpoint)

def auth_error(user_desc = None, dev_desc = None):
    # log stuff
    if dev_desc != None:
        rc.application.logger.debug('Auth error: %s', dev_desc)
    
    # set user message
    if user_desc != None:
        rc.user.add_message('error', user_desc)
        
    # forward to fatal error view
    rc.controller.forward(rc.application.settings.sys_auth_error_endpoint)

def bad_request_error(dev_desc = None):
    # log stuff
    if dev_desc != None:
        rc.application.logger.debug('bad request error: %s', dev_desc)
        
    # forward to fatal error view
    rc.controller.forward(rc.application.settings.bad_request_error_endpoint)

# from sqlalchemy
def tolist(x, default=None):
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
    print pp.pprint(stuff)

def load_appmod_models(singlemod=None):
    for module in rc.application.settings.modules:
        if singlemod == module or singlemod == '':
            try:
                rc.application.loader.appmod_names('%s.model' % module, [])
            except ImportError:
                pass

def call_appmod_dbinits(singlemod=None):
    for module in rc.application.settings.modules:
        if singlemod == module or singlemod == '':
            try:
                callables = rc.application.loader.appmod_names('%s.settings' % module, 'appmod_dbinits')
                for tocall in tolist(callables):
                    tocall()
            except ImportError:
                pass
        
def call_appmod_inits(module):
    """ call the initilization methods on an AM """
    callables = rc.application.loader.appmod_names('%s.settings' % module, 'appmod_inits')
    for tocall in tolist(callables):
            tocall()
        
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
        if 'debug' in rc.application.settings.logging_levels:
            d = {'request_ident':rc.ident}
            kwargs['extra'] = d
            self.dlogger.debug(msg, *args, **kwargs)
    
    def info(self, msg):
        if 'info' in rc.application.settings.logging_levels:
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