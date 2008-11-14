#!/usr/bin/env python
# -*- coding: utf-8 -*-

from os import path
from pysmvt import config
from pysmvt.application import Application
import settings

def makeapp(profile='Default', **kwargs):
    
    config.appinit(settings, profile, **kwargs)
    
    app = Application()
    
    return app