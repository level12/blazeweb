from blazeweb.config import ComponentSettings

class Settings(ComponentSettings):

    def init(self):
        self.for_me.noroutes = True
