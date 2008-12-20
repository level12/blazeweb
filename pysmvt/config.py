# -*- coding: utf-8 -*-
from os import path
import os
import logging
import re
from pysmvt import appimport, settings, ag, modimport
from werkzeug.routing import Rule, Map, Submount
from pysmvt.utils import OrderedProperties, OrderedDict, Context, tb_depth_in
from pysmvt.utils.filesystem import mkdirs
from pysmvt.exceptions import SettingsError
from pysutils import case_us2cw, multi_pop

class QuickSettings(OrderedProperties):
    def __init__(self, initialize=True):
        self._locked = False
        OrderedProperties.__init__(self, initialize)
    
    def lock(self):
        self._locked = True
        for child in self._data.values():
            if isinstance(child, QuickSettings):
                child.lock()
    
    def unlock(self):
        self._locked = False
        for child in self._data.values():
            if isinstance(child, QuickSettings):
                child.unlock()
    
    def __getattr__(self, key):
        if not self._data.has_key(key):
            if not self._locked:
                self._data[key] = QuickSettings()
            else:
                raise AttributeError("object has no attribute '%s' (object is locked)" % key)
        return self._data[key]
    
    def update(self, ____sequence=None, **kwargs):
        if ____sequence is not None:
            if hasattr(____sequence, 'keys'):
                for key in ____sequence.keys():
                    try:
                        self.get(key).update(____sequence[key])
                    except (AttributeError, ValueError), e:
                        if "object has no attribute 'update'" not in str(e) and "need more than 1 value to unpack" not in str(e):
                            raise
                        self.__setitem__(key, ____sequence[key])
            else:
                for key, value in ____sequence:
                    self[key] = value
        if kwargs:
            self.update(kwargs)

class ModulesSettings(QuickSettings):
    """
        a custom settings object for settings.modules.  The only difference
        is that when iterating over the object, only modules with
        .enabled = True are returned.
    """
    def _set_data_item(self, item, value):
        if not isinstance(value, QuickSettings):
            raise TypeError('all values set on ModuleSettings must be a QuickSettings object')
        QuickSettings._set_data_item(self, item, value)

    def __len__(self):
        return len(self.keys())

    def iteritems(self, showinactive=False):
        for k,v in self._data.iteritems():
            try:
                if showinactive or v.enabled == True:
                    yield k,v
            except AttributeError, e:
                if "object has no attribute 'enabled'" not in str(e):
                    raise
            
    def __iter__(self):
        for v in self._data.values():
            try:
                if v.enabled == True:
                    yield v
            except AttributeError, e:
                if "object has no attribute 'enabled'" not in str(e):
                    raise

    def __contains__(self, key):
        return key in self.todict()

    def keys(self, showinactive=False):
        return [k for k,v in self.iteritems(showinactive)]
    
    def values(self, showinactive=False):
        return [v for k,v in self.iteritems(showinactive)]
    
    def todict(self, showinactive=False):
        if showinactive:
            return self._data
        d = OrderedDict()
        for k,v in self.iteritems():
            d[k] = v
        return d

class DefaultSettings(QuickSettings):
    
    def __init__(self, appname,  basedir):
        QuickSettings.__init__(self)
        
        # name of the primary application
        self.appname = appname
        
        # supporting applications
        self.supporting_apps = []
        
        # application modules from our application or supporting applications
        self.modules = ModulesSettings()
        
        #######################################################################
        # ROUTING
        #######################################################################
        self.routing.routes = [
            # a special route for testing purposes
            Rule('/[pysmvt_test]', endpoint='[pysmvt_test]')
        ]
        
        # note that you shouldn't really need to use the routing prefix if
        # SCRIPT_NAME and PATH_INFO are set correctly as the Werkzeug
        # routing tools (both parsing rules and generating URLs) will
        # take these environment variables into account.
        self.routing.prefix = ''
        
        # the settings for the Werkzeug routing Map object:
        self.routing.map.default_subdomain=''
        self.routing.map.charset='utf-8'
        self.routing.map.strict_slashes=True
        self.routing.map.redirect_defaults=True
        self.routing.map.converters=None
        
        #######################################################################
        # DIRECTORIES required by PYSVMT
        #######################################################################
        self.dirs.base = basedir
        self.dirs.writeable = path.join(basedir, 'writeable')
        self.dirs.static = path.join(basedir, 'static')
        self.dirs.templates = path.join(basedir, 'templates')
        self.dirs.data = path.join(self.dirs.writeable, 'data')
        self.dirs.logs = path.join(self.dirs.writeable, 'logs')
        self.dirs.tmp = path.join(self.dirs.writeable, 'tmp')
        
        #######################################################################
        # SESSIONS
        #######################################################################
        #beaker session options
        #http://wiki.pylonshq.com/display/beaker/Configuration+Options
        self.beaker.type = 'dbm'
        self.beaker.data_dir = path.join(self.dirs.tmp, 'session_cache')
        
        #######################################################################
        # TEMPLATES
        #######################################################################
        self.template.default = 'default.html'
        
        #######################################################################
        # SYSTEM VIEW ENDPOINTS
        #######################################################################
        self.endpoint.sys_error = ''
        self.endpoint.sys_auth_error = ''
        self.endpoint.bad_request_error = ''
        
        #######################################################################
        # EXCEPTION HANDLING
        #######################################################################
        # if True, most exceptions will be caught and
        # turned into a 500 response, which will optionally be handled by
        # the error docs handler if setup for 500 errors
        #
        #  *** SET TO True FOR PRODUCTION ENVIRONMENTS ***
        self.exceptions.hide = False
        # if true, an email will be sent using mail_programmers() whenever
        # an exception is encountered
        self.exceptions.email = False
        # if True, will send exception details to the applications debug file
        self.exceptions.log = True
        
        #######################################################################
        # DEBUGGING
        #######################################################################
        # only matters when exceptions.hide = False.  Setting interactive =
        # to True will give a python command prompt in the stack trace
        #
        #          ******* SECURITY ALERT **********
        # setting interactive = True would allow ANYONE who has http access to the 
        # server to run arbitrary code.  ONLY use in an isolated development
        # environment.
        self.debugger.enabled = True
        self.debugger.interactive = False
        
        #######################################################################
        # EMAIL ADDRESSES
        #######################################################################
        # the 'from' address used by mail_admins() and mail_programmers()
        # defaults if not set
        self.emails.from_server = ''
        # the default 'from' address used if no from address is specified
        self.emails.from_default = ''
        # a default reply-to header if one is not specified
        self.emails.reply_to = ''
        
        ### recipient defaults.  Should be a list of email addresses
        ### ('foo@example.com', 'bar@example.com')
        
        # will always add theses cc's to every email sent
        self.emails.cc_always = None
        # default cc, but can be overriden
        self.emails.cc_defaults = None
        # will always add theses bcc's to every email sent
        self.emails.bcc_always = None
        # default bcc, but can be overriden
        self.emails.bcc_defaults = None
        # programmers who would get system level notifications (code
        # broke, exception notifications, etc.)
        self.emails.programmers = None
        # people who would get application level notifications (payment recieved,
        # action needed, etc.)
        self.emails.admins = None
        # a single or list of emails that will be used to override every email sent
        # by the system.  Useful for debugging.  Original recipient information
        # will be added to the body of the email
        self.emails.override = None
        
        #######################################################################
        # EMAIL SETTINGS
        #######################################################################
        # used by mail_admins() and mail_programmers()
        self.email.subject_prefix = ''
        
        #######################################################################
        # SMTP SETTINGS
        #######################################################################
        self.smtp.host = 'localhost'
        self.smtp.port = 25
        self.smtp.user = ''
        self.smtp.password = ''
        self.smtp.use_tls = False
        
        #######################################################################
        # OTHER DEFAULTS
        #######################################################################
        self.default_charset = 'utf-8'
        self.default.file_mode = 0640
        self.default.dir_mode = 0750
        
        #######################################################################
        # ERROR DOCUMENTS
        #######################################################################
        # you can set endpoints here that will be used if an error response
        # is detected to try and give the user a more consistent experience
        # self.error_docs[404] = 'errorsmod:NotFound'
        self.error_docs

def appinit(settings_mod=None, profile=None, settings_cls=None):
    """
        called to setup the application's settings
        variable
    """
    if settings_cls is None:
        Settings = getattr(settings_mod, profile)
    else:
        Settings = settings_cls
    settings._push_object(Settings())
    ag._push_object(Context())

    ## setup python logging based on settings configuration
    level1map = {
            'critical':logging.CRITICAL,
            'fatal':logging.FATAL,
            'error':logging.ERROR,
            'warning':logging.WARNING,
            'warn':logging.WARN,
            'info':logging.INFO,
            'debug':logging.DEBUG,
        }
    
    keywords = 'enabled', 'filter', 'date_format', 'format'
    # logging is only enabled if there is a logging key and it is not disabled
    if settings.has_key('logging') and settings.logging.get('enabled', True):
        for level1 in settings.logging.keys():
            l1_value = settings.logging[level1]
            
            #print 'l1 %s:%s' % (level1, l1_value)
            #setup our regular expression
            p = re.compile(r'L\d\d?$')
            match = p.match(level1)
            if level1.lower() in level1map:
                logger_level = level1map[level1.lower()]
            elif match:
                logger_level = int(match.group().lstrip('L'))
                if logger_level < 0 or logger_level > 50:
                    SettingsError('Invalid logging key: %s'%level1)
            elif level1 in keywords:
                if level1 == 'filter':
                    default_filter = logging.Filter(settings.logging.filter)
                    continue
                elif level1 == 'format':
                    default_format = logging.Formatter(settings.logging.format)
                    continue
                elif level1 == 'date_format':
                    # need something here to set default_date_format
                    continue
                else:
                    continue
            else:
                raise SettingsError('Invalid logging key: %s'%level1)
            
            # at this point, we know that this entry is actually
            # a logging level.  Has this logging level been disabled?
            if not l1_value.get('enabled', True):
                continue
            # we can now setup the logger for this level
            logger = logging.getLogger()
            logger.setLevel(logger_level)
            
            # this logging level can have default settings for all the handlers
            # as well as having the handler definitions themselves
            for l2_key in l1_value.keys():
                l2_value = l1_value[l2_key]
                #print 'l2 %s:%s' % (l2_key, l2_value.todict())
                
                # we don't want to add hanlders for keywords, so just continue
                if l2_key in keywords:
                    continue
                
                # l2_key is not in the keywords, so we assume it is a short
                # handler name.  Convert that to an actual handler name
                handler_name = case_us2cw(l2_key) + 'Handler'
                if not hasattr(logging, handler_name):
                    raise SettingsError('Invalid handler: %s'%l2_key)
                    
                # pop the keyword values out of the handler args
                handler_args = l2_value.todict()
                handler_kw = multi_pop(handler_args, *keywords)
                
                # has this handler been disabled?
                if not handler_kw.get('enabled', True):
                    continue
       
                # instantiate the handler with the args left over
                handler = getattr(logging, handler_name)(**handler_args)
                # determine filter/formatter settings from defaults
                filter = (handler_kw.get('filter') or
                          l1_value.get('filter') or
                           settings.logging.get('filter'))
                format = (handler_kw.get('format') or
                          l1_value.get('format') or
                           settings.logging.get('format'))
                date_format = (handler_kw.get('date_format') or
                          l1_value.get('date_format') or
                           settings.logging.get('date_format'))

                if filter:
                    handler.addFilter(logging.Filter(filter))
                if format or date_format:
                    handler.setFormatter(logging.Formatter(format, date_format))
                logger.addHandler(handler)
    
    # create the writeable directories if they don't exist already
    mkdirs(settings.dirs.data)
    mkdirs(settings.dirs.logs)
    mkdirs(settings.dirs.tmp)
    
    # now we need to assign module settings to the main setting object
    for module in settings.modules.keys():
        try:
            Settings = modimport('%s.settings' % module, 'Settings')
            ms = Settings()
            # update the module's settings with any module level settings made
            # at the app level.  This allows us to override module settings
            # in our applications settings.py file.
            ms.update(settings.modules[module])
            settings.modules[module] = ms
        except ImportError:
            # 3 = .settings or Settings wasn't found, which is ok.  Any other
            # depth means a different import error, and we want to raise that
            if not tb_depth_in(3):
                raise
    
    # lock the settings, this ensures that an attribute error is thrown if an
    # attribute is accessed that doesn't exist.  Without the lock, a new attr
    # would be created, which is undesirable since any "new" attribute at this
    # point would probably be an accident
    settings.lock()
    
    ###
    ### routing
    ###
    ag.route_map = Map(**settings.routing.map.todict())
       
    # application routes
    _add_routing_rules(settings.routing.routes)
   
    # module routes        
    for module in settings.modules:
        if hasattr(module, 'routes'):
            _add_routing_rules(module.routes)

def _add_routing_rules(rules):
    if settings.routing.prefix:
        # prefix the routes with the prefix in the app settings class
        ag.route_map.add(Submount( settings.routing.prefix, rules ))
    else:
        for rule in rules or ():
            ag.route_map.add(rule)

def appslist(reverse=False):
    if reverse:
        apps = list(settings.supporting_apps)
        apps.reverse()
        apps.append(settings.appname)
        return apps
    return [settings.appname] + settings.supporting_apps
