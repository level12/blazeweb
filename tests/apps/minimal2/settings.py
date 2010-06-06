from os import path

from pysmvt.config import DefaultSettings

basedir = path.dirname(__file__)
appname = path.basename(basedir)

class Default(DefaultSettings):
    def init(self):
        self.dirs.base = basedir
        self.appname = appname
        DefaultSettings.init(self)

class Test(Default):
    def init(self):
        Default.init(self)
        
        self.apply_test_settings()
        print 'Test settings'

class Test2(Default):
    def init(self):
        Default.init(self)
        
        self.apply_test_settings()
        print 'Test2 settings'