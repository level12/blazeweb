#!/usr/bin/env python
# -*- coding: utf-8 -*-

from os import path
from pysmvt.application import Application
import settings


class Webapp(Application):
    
    def __init__(self, profile='default'):
        
        #set the applications base file path
        self.basedir = path.dirname(path.abspath(__file__))
        
        # initilize the application
        Application.__init__(self, 'pysmvttestapp2', settings, profile)