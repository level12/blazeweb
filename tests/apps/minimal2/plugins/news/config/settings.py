from blazeweb.config import PluginSettings

class Settings(PluginSettings):

    def init(self):
        # plugin-specific
        self.for_me.min2news = 'internal'

        # put something at the application level for testing
        self.for_app.setting_from_plugin = 'minimal2'

        # add a value to the app's current settings
        self.app_settings.some_list.append('minimal2')
