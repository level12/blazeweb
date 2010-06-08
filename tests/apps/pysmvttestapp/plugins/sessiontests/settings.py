from werkzeug.routing import Rule

from pysmvt.config import QuickSettings

class Settings(QuickSettings):
    
    def __init__(self):
        QuickSettings.__init__(self)
        
        self.routes = ([
            Rule('/sessiontests/setfoo', endpoint='sessiontests:SetFoo'),
            Rule('/sessiontests/getfoo', endpoint='sessiontests:GetFoo'),
        ])