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
        