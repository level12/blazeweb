from pysmvt.config import PluginSettings

class Settings(PluginSettings):

    def init(self):

        self.add_route('/fake/route', 'news:notthere')
        self.add_route('/news', 'news:Index')
        self.add_route('/forwardwithargs', 'news:ForwardWithArgs')

        self.foo = 1
        self.bar = 2
