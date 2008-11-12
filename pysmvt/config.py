# -*- coding: utf-8 -*-
from os import path
import os
from werkzeug.routing import Rule
from pysmvt.utils import OrderedProperties, OrderedDict

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
        self.modules
        
        #######################################################################
        # ROUTING
        #######################################################################
        self.routing.routes = [
            Rule('/static/<file>', endpoint='static', build_only=True),
            Rule('/static/c/<file>', endpoint='styles', build_only=True),
            Rule('/static/js/<file>', endpoint='javascript', build_only=True),
            Rule('/<app>/static/c/<file>', endpoint='styles', build_only=True),
            Rule('/<app>/static/js/<file>', endpoint='javascript', build_only=True)
        ]
        self.routing.prefix = ''
        
        #######################################################################
        # DATABASE
        #######################################################################
        self.db.echo = False
        self.db.uri = None
        
        #######################################################################
        # DIRECTORIES required by PYSVMT
        #######################################################################
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
        self.template.admin = 'admin.html'
        
        #######################################################################
        # SYSTEM VIEW ENDPOINTS
        #######################################################################
        self.endpoint.sys_error = ''
        self.endpoint.sys_auth_error = ''
        self.endpoint.bad_request_error = ''
        
        #######################################################################
        # EXCEPTION HANDLING
        #######################################################################
        self.views.trap_exceptions = False
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
        # only matters when exceptions.hide = False.  Possible values:
        # 'standard' : shows a formatted stack trace in the browser
        # 'interactive' : like standard, but has an interactive command line
        #
        #          ******* SECURITY ALERT **********
        # setting to 'inactive' would allow ANYONE who has access to the server
        # to run arbitrary code.  ONLY use in an isolated development
        # environment
        self.debugger.enabled = True
        self.debugger.format = 'standard'

        #######################################################################
        # LOGGING
        #######################################################################
        # currently support 'debug' & 'info'
        self.logging.levels = []
        
        #######################################################################
        # EMAIL ADDRESSES
        #######################################################################
        # the 'from' address used by mail_admins() and mail_programmers()
        # defaults if not set
        self.emails.from_server = 'root@server'
        # the default 'from' address used if no from address is specified
        self.emails.from_default = 'root@localhost'
        # a default reply-to header if one is not specified
        self.emails.reply_to = ''
        
        # recipient defaults.  Should be a list of email addresses
        # ('foo@example.com', 'bar@example.com')
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
        # ENCODING
        #######################################################################
        self.default_charset = 'utf-8'
        
        #######################################################################
        # ERROR DOCUMENTS
        #######################################################################
        # you can set endpoints here that will be used if an error response
        # is detected to try and give the user a more consistent experience
        # self.error_docs[404] = 'errorsmod:NotFound'
        self.error_docs

