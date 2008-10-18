# -*- coding: utf-8 -*-
from os import path
from werkzeug.routing import Rule
from pysmvt.settings import Base

class Default(Base):

    def __init__(self):
        # call parent init to setup default settings
        Base.__init__(self)
        
        # we are done adding variables to this settings object, so lock it
        self.lock()
