# -*- coding: utf-8 -*-
from os import path
from werkzeug.routing import Rule
from pysmvt.config import DefaultSettings

appname = 'pysmvttestapp2'
basedir = path.dirname(path.abspath(__file__))

class Default(DefaultSettings):

    def __init__(self):
        # call parent init to setup default settings
        DefaultSettings.__init__(self, appname, basedir)

class Testruns(DefaultSettings):
    def __init__(self):
        # call parent init to setup default settings
        DefaultSettings.__init__(self, appname, basedir)
        
        self.routing.routes.extend([
            Rule('/', endpoint='tests:Index')
        ])

        self.modules.tests.enabled = True

        # don't use exception catching, debuggers, logging, etc.
        self.apply_test_settings()
        
        self.emails.programmers = ['randy@rcs-comp.com']
        self.email.subject_prefix = '[pysvmt test app] '
        