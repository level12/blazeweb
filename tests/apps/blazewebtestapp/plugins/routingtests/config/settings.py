from blazeweb.config import PluginSettings

class Settings(PluginSettings):

    def init(self):

        self.add_route('/routingtests/currenturl', 'routingtests:CurrentUrl')
