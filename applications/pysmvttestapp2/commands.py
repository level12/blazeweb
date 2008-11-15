#!/usr/bin/env python
# -*- coding: utf-8 -*-

from os import path
from beaker.middleware import SessionMiddleware
from paste.registry import RegistryManager
from paste.cascade import Cascade
from pysmvt import config, settings
from pysmvt.application import Application
from pysmvt.middleware import ElixirApp
from pysmvt import routing
from werkzeug import SharedDataMiddleware
import settings as settingsmod

def makeapp(profile='Default', **kwargs):
    
    config.appinit(settingsmod, profile, **kwargs)
    
    app = Application()
    
    app = ElixirApp(app)
    
    #app = ExceptionHandler(app)
    
    #app = ErrorDocuments(app)
    
    #app = ForwardHandler(app)
    
    app = SessionMiddleware(app, **dict(settings.beaker))
    
    app = RegistryManager(app)
    
    # for serving plain html, css, images, etc.
    static_map = {
            routing.add_prefix('/static'):     settings.dirs.static
        }
    for sapp in settings.supporting_apps:
        app_py_mod = __import__(sapp)
        fs_static_path = path.join(path.dirname(app_py_mod.__file__), 'static')
        static_map[routing.add_prefix('/%s/static' % sapp)] = fs_static_path
    staticapp = SharedDataMiddleware(app, static_map)
    
    # look for something in the static area first, if not found there, then
    # forward on to the application stack
    app = Cascade([staticapp, app])
    
    # show nice stack traces and debug output if enabled
    if settings.debugger.enabled:
        app = DebuggedApplication(app, evalex=settings.debugger.interactive)
    
    return app