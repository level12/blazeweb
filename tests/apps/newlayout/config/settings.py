from os import path

from nlsupporting.config.settings import Default as nlDefault

basedir = path.dirname(path.dirname(__file__))
appname = path.basename(basedir)

class Default(nlDefault):
    def init(self):
        self.dirs.base = basedir
        self.appname = appname
        nlDefault.init(self)

        self.supporting_apps.append('nlsupporting')
        self.setup_plugins()

        self.plugins.news.bar = 3

    def get_storage_dir(self):
        return path.join(basedir, '..', '..', 'test-output', appname)

    def setup_plugins(self):
        """
            plugins need to be in order of importance, so supporting apps
            need to setup their plugins later
        """
        self.add_plugin(appname, 'news', 'newsplug1')
        self.add_plugin(appname, 'news', 'newsplug2')
        self.add_plugin(appname, 'pdisabled')
        self.pluginmap.newlayout.pdisabled.enabled = False
        self.add_plugin(appname, 'badimport')

        nlDefault.setup_plugins(self)
