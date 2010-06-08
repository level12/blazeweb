from werkzeug.routing import Rule

from pysmvt.config import QuickSettings

class Settings(QuickSettings):

    def __init__(self):
        QuickSettings.__init__(self)

        self.routes = ([
            Rule('/fake/route', endpoint='news:notthere'),
        ])

        self.foo = 1
        self.bar = 2
