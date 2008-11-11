# -*- coding: utf-8 -*-
from os import path
import os
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

