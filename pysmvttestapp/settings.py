# -*- coding: utf-8 -*-
from os import path
from werkzeug.routing import Rule
from pysmvt.config import DefaultSettings

appname = 'pysmvttestapp'
basedir = path.dirname(path.abspath(__file__))

class Default(DefaultSettings):

    def __init__(self):
        # call parent init to setup default settings
        DefaultSettings.__init__(self, appname, basedir)

class Testruns(DefaultSettings):
    def __init__(self):
        # call parent init to setup default settings
        DefaultSettings.__init__(self, appname, basedir)
        
        self.supporting_apps = ['pysmvttestapp2']
        
        self.modules.tests.enabled = True
        self.modules.nomodel.enabled = True
        self.modules.nosettings.enabled = True
        self.modules.sessiontests.enabled = True
        self.modules.usertests.enabled = True
        self.modules.routingtests.enabled = True
        self.modules.disabled.enabled = False
        
        self.routing.routes.extend([
            Rule('/', endpoint='tests:Index')
        ])
        
        self.db.url = 'sqlite:///'
        
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
        self.debugger.enabled = False
        self.debugger.format = 'interactive'
        
        
        self.emails.programmers = ['randy@rcs-comp.com']
        self.email.subject_prefix = '[pysvmt test app] '
        
        # a fake setting for testing
        self.foo = 'bar'
        
        # logging
        #self.logging.debug.stream.filter = 'pysmvt'

class NoLogs(Testruns):
    def __init__(self):
        Testruns.__init__(self)
        
        self.logs.errors.enabled = False
        self.logs.application.enabled = False
        self.logs.null_handler.enabled = True
        