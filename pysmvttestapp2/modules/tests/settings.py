from werkzeug.routing import Rule

from pysmvt.config import QuickSettings

class Settings(QuickSettings):
    
    def __init__(self):
        QuickSettings.__init__(self)
        
        self.routes = ([
            Rule('/tests/rvbapp2', endpoint='tests:Rvb'),
            Rule('/tests/underscoretemplates', endpoint='tests:UnderscoreTemplates'),
        ])