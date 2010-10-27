from blazeweb.config import ComponentSettings

class Settings(ComponentSettings):

    def init(self):
        self.add_route('/foo', 'foo:UserUpdate')
        self.for_me.fooattr = True
