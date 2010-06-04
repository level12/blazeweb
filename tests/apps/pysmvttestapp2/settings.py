# -*- coding: utf-8 -*-
from os import path
from werkzeug.routing import Rule
from pysmvt.config import DefaultSettings

class Default(DefaultSettings):
    def init(self):
        self.dirs.base = path.dirname(__file__)
        self.appname = path.basename(self.dirs.base)
        DefaultSettings.init(self)

class Testruns(Default):
    def init(self):
        Default.init(self)
        
        self.routing.routes.extend([
            Rule('/', endpoint='tests:Index')
        ])

        self.modules.tests.enabled = True

        # don't use exception catching, debuggers, logging, etc.
        self.apply_test_settings()
        
        self.emails.programmers = ['you@example.com']
        self.email.subject_prefix = '[pysvmt test app] '
        