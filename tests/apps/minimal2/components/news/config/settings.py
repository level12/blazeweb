from blazeweb.config import ComponentSettings

class Settings(ComponentSettings):

    def init(self):
        # component-specific
        self.for_me.min2news = 'internal'

        # put something at the application level for testing
        self.for_app.setting_from_component = 'minimal2'

        # add a value to the app's current settings
        self.app_settings.some_list.append('minimal2')
