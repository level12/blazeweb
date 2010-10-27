from os import path

from blazeweb.config import DefaultSettings

basedir = path.dirname(path.dirname(__file__))
app_package = path.basename(basedir)

class Default(DefaultSettings):

    def setup_components(self):
        self.add_component(app_package, 'news')
        self.add_component(app_package, 'news', 'newscomp3')
