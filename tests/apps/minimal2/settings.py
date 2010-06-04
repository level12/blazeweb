from os import path

from pysmvt.config import DefaultSettings

basedir = path.dirname(__file__)
appname = path.basename(basedir)

class Default(DefaultSettings):
    def init(self):
        self.dirs.base = basedir
        self.appname = appname
        DefaultSettings.init(self)


