from blazeweb.config import PluginSettings

class Settings(PluginSettings):

    def init(self):
        self.add_route('/foo', 'foo:UserUpdate')
        self.for_me.fooattr = True
