from os import path

from pysmvt.config import DefaultSettings

basedir = path.dirname(path.dirname(__file__))
appname = path.basename(basedir)

class Default(DefaultSettings):
        
    def setup_plugins(self):
        self.add_plugin(appname, 'news', 'newsplug3')
        
