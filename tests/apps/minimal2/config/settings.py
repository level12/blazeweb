from os import path

from blazeweb.config import DefaultSettings

basedir = path.dirname(path.dirname(__file__))
app_package = path.basename(basedir)

class Default(DefaultSettings):
    def init(self):
        self.dirs.base = basedir
        self.app_package = app_package
        DefaultSettings.init(self)

        # since this is a quick start app, we want our views.py file to get
        # loaded
        self.auto_load_views = True

    def get_storage_dir(self):
        return path.join(basedir, '..', '..', 'test-output', app_package)

class Dev(Default):
    def init(self):
        Default.init(self)
        self.apply_dev_settings()

class Dispatching(Default):

    def init(self):
        Default.init(self)
        self.apply_test_settings()
        self.static_files.enabled = False

        self.add_plugin(self.app_package, 'internalonly')
        self.add_plugin(self.app_package, 'news')
        self.add_plugin(self.app_package, 'news', 'newsplug4')
        self.add_plugin(self.app_package, 'foo', 'foobwp')

class EventSettings(Default):
    def init(self):
        Default.init(self)
        self.apply_test_settings()

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

class TestStorageDir(Default):
    def init(self):
        Default.init(self)

        self.apply_test_settings()
        self.auto_create_writeable_dirs = False

    def get_storage_dir(self):
        return DefaultSettings.get_storage_dir(self)

class NoAutoImportView(Default):
    def init(self):
        Default.init(self)

        self.apply_test_settings()

        # we just want to make sure turning the setting off works too
        self.auto_load_views = False
