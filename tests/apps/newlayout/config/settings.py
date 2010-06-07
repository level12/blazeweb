from os import path

from pysmvt.config import DefaultSettings

basedir = path.dirname(path.dirname(__file__))
appname = path.basename(basedir)

class Default(DefaultSettings):
    def init(self):
        self.dirs.base = basedir
        self.appname = appname
        DefaultSettings.init(self)
        
        self.plugins.news.enabled = True
        self.plugins.news.packages = 'newsplug1', 'newsplug2'
        self.plugins.pdisabled.enabled = False
        self.plugins.badimport.enabled = True
        
        nls = self.add_app('nlsupporting')
        nls.plugins.news.enabled = True
        nls.plugins.news.packages = 'newsplug3'
        
