from blazeweb.config import PluginSettings

class Settings(PluginSettings):

    def init(self):

        self.add_route('/sessiontests/setfoo', 'sessiontests:SetFoo')
        self.add_route('/sessiontests/getfoo', 'sessiontests:GetFoo')
