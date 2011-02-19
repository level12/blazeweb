from blazeweb.config import ComponentSettings

class Settings(ComponentSettings):

    def init(self):

        self.add_route('/sessiontests/setfoo', 'sessiontests:SetFoo')
        self.add_route('/sessiontests/getfoo', 'sessiontests:GetFoo')
        self.add_route('/sessiontests/regenid', 'sessiontests:RegenId')
