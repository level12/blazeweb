from pysmvt.config import PluginSettings

class Settings(PluginSettings):

    def init(self):
        PluginSettings.init(self)
        self.add_route('/foo', 'foo:UserUpdate')
        self.fooattr = True
