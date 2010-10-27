from werkzeug.routing import Rule

from blazeweb.config import ComponentSettings

class Settings(ComponentSettings):

    def init(self):
        self.for_me.routes = ([
            Rule('/tests/rvbapp2', endpoint='tests:Rvb'),
            Rule('/tests/underscoretemplates', endpoint='tests:UnderscoreTemplates'),
        ])
