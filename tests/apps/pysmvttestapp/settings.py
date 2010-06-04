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
        
        # don't use exception catching, debuggers, logging, etc.
        self.apply_test_settings()        
        
        self.emails.programmers = ['randy@rcs-comp.com']
        self.email.subject_prefix = '[pysvmt test app] '
        
        # a fake setting for testing
        self.foo = 'bar'

class WithLogs(Testruns):
    def __init__(self):
        Testruns.__init__(self)
        
        self.logs.enabled = True
        