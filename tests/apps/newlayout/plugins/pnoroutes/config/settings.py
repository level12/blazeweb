from blazeweb.config import PluginSettings

class Settings(PluginSettings):

    def init(self):
        self.for_me.noroutes = True
