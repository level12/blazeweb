from werkzeug.routing import Rule

from pysmvt.utils import QuickSettings, pprint

class Settings(QuickSettings):
    
    def __init__(self):
        QuickSettings.__init__(self)
        
        self.routes = ([
            Rule('/tests/rvb', endpoint='tests:Rvb'),
            Rule('/tests/rvbwsnip', endpoint='tests:RvbWithSnippet'),
        ])
        
        # no more values can be added
        self.lock()