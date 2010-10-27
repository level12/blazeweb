from os import path

from nlsupporting.config.settings import Default as nlDefault

basedir = path.dirname(path.dirname(__file__))
app_package = path.basename(basedir)

class Default(nlDefault):
    def init(self):
        self.dirs.base = basedir
        self.app_package = app_package
        nlDefault.init(self)

        self.add_route('/applevelview/<v1>', 'AppLevelView')
        self.add_route('/index/<tname>', 'Index')
        self.add_route('/abort/<tname>', 'Abort')
        self.add_route('/eventtest', 'EventTest')
        self.add_route('/request-hijack/<sendtype>', 'None')

        self.supporting_apps.append('nlsupporting')
        self.setup_components()

        # don't use exception catching, debuggers, logging, etc.
        self.apply_test_settings()

        # application level setting should take precedence over what is defined
        # in the component's settings file
        self.components.news.bar = 3

    def get_storage_dir(self):
        return path.join(basedir, '..', '..', 'test-output', app_package)

    def setup_components(self):
        """
            components need to be in order of importance, so supporting apps
            need to setup their components later
        """
        self.add_component(app_package, 'news')
        self.add_component(app_package, 'news', 'newscomp1')
        self.add_component(app_package, 'news', 'newscomp2')
        self.add_component(app_package, 'pdisabled')
        self.add_component(app_package, 'pnoroutes')
        self.componentmap.newlayout.pdisabled.enabled = False
        self.add_component(app_package, 'badimport')

        nlDefault.setup_components(self)

class AutoCopyStatic(Default):
    def init(self):
        Default.init(self)
        self.auto_copy_static.enabled = True

class WithTestSettings(Default):
    def init(self):
        Default.init(self)
        self.auto_abort_as_builtin = True

class ForStaticFileTesting(Default):
    def init(self):
        Default.init(self)
        self.static_files.location  = 'source'

class AttributeErrorInSettings(Default):
    def init(self):
        Default.init(self)
        print path.notthere
