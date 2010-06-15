from pysmvt.config import PluginSettings

class Settings(PluginSettings):

    def __init__(self):
        PluginSettings.__init__(self)

        self.add_route('/foo', 'foo:UserUpdate', id=None)
