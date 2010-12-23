from os import path
from blazeweb.config import DefaultSettings
from blazeweb.events import settings_connect

class Settings(DefaultSettings):
    def init(self):
        self.dirs.base = path.dirname(__file__)
        self.app_package = path.basename(self.dirs.base)
        DefaultSettings.init(self)
        # don't use exception catching, debuggers, logging, etc.
        self.apply_test_settings()

    def get_storage_dir(self):
        return path.join(self.dirs.base, '..', '..', 'test-output', self.app_package)

    @settings_connect('blazeweb.logging.initialized')
    def connected_method(self, sender):
        self.logging_is_initialized = True

    @property
    def foobar(self):
        # this test makes sure we don't get side effects from the applications
        # search for settings_connect() decorated functions
        raise ValueError('this shouldn\'t have been called')
