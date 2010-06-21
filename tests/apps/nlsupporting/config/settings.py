from os import path

from blazeweb.config import DefaultSettings

basedir = path.dirname(path.dirname(__file__))
app_package = path.basename(basedir)

class Default(DefaultSettings):

    def setup_plugins(self):
        self.add_plugin(app_package, 'news')
        self.add_plugin(app_package, 'news', 'newsplug3')
