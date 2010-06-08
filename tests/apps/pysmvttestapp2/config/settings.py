# -*- coding: utf-8 -*-
from os import path
from werkzeug.routing import Rule
from pysmvt.config import DefaultSettings

basedir = path.dirname(path.dirname(__file__))
appname = path.basename(basedir)

class Default(DefaultSettings):
    def init(self):
        self.dirs.base = basedir
        self.appname = appname
        DefaultSettings.init(self)

class Testruns(Default):
    def init(self):
        Default.init(self)

        self.routing.routes.extend([
            Rule('/', endpoint='tests:Index')
        ])

        self.add_plugin(appname, 'tests')

        # don't use exception catching, debuggers, logging, etc.
        self.apply_test_settings()

        self.emails.programmers = ['you@example.com']
        self.email.subject_prefix = '[pysvmt test app] '
