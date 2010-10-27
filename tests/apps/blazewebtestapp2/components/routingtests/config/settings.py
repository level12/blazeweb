from blazeweb.config import ComponentSettings

class Settings(ComponentSettings):

    def init(self):

        self.add_route('/routingtests/currenturl', 'routingtests:CurrentUrl')
