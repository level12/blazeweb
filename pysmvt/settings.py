# -*- coding: utf-8 -*-
from os import path
import os
import logging
from werkzeug.routing import Rule
from pysmvt.application import request_context as rc
from pysmvt.utils import QuickSettings

class Base(QuickSettings):
    
    def __init__(self):
        QuickSettings.__init__(self)
        
        # supporting applications
        self.supporting_apps = []
        
        # application modules from our application or supporting applications
        self.modules
        
        #######################################################################
        # ROUTING
        #######################################################################
        self.routing.routes = []
        self.routing.prefix = ''
        
        #######################################################################
        # DATABASE
        #######################################################################
        self.db.echo = False
        self.db.uri = None
        
        #######################################################################
        # DIRECTORIES required by PYSVMT
        #######################################################################
        baseDir = rc.application.baseDir
        self.dirs.writeable = path.join(baseDir, 'writeable')
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
        # LOGGING & DEBUG
        #######################################################################
        # currently support 'debug' & 'info'
        self.logging.levels = logging.NOTSET
        self.views.trap_exceptions = False
        self.controller.hide_exceptions = False
        
        #######################################################################
        # EMAIL ADDRESSES
        #######################################################################
        self.emails.server_from = 'root@localhost'
        self.emails.default_from = 'root@localhost'
        self.emails.reply_to = ''
        # recipient defaults.  Should be able to accept a list of email addresses
        # ('foo@example.com', 'bar@example.com') or a double list of names/email
        # addresses (('Full Name', 'foo@example.com'), ('Full Name', 'bar@example.com'))
        self.emails.cc = None
        self.emails.bcc = None
        # programmers who would get system level notifications (code
        # broke, exception notifications, etc.)
        self.emails.programmers = None
        # a list of emails that will be used to override every email sent
        # by the system.  Useful for debugging.
        self.emails.overrides = None
        # people who would get application level notifications (payment recieved,
        # action needed, etc.)
        self.emails.admins = None
        
        #######################################################################
        # EMAIL
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
        