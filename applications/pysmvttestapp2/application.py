#!/usr/bin/env python
# -*- coding: utf-8 -*-

from os import path
from pysmvt.application import Application
import settings


class Webapp(Application):
    
    def __init__(self, profile='default'):
        
        #set the applications base file path
        self.baseDir = path.dirname(path.abspath(__file__))
        
        #set the name of the application's package
        self.appPackage = 'pysmvttestapp2'
        
        # initilize the application
        Application.__init__(self, settings, profile)