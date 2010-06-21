from werkzeug.routing import Rule

from blazeweb.config import QuickSettings

class Settings(QuickSettings):
    
    def __init__(self):
        QuickSettings.__init__(self)
        
        self.routes = []