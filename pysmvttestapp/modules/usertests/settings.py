from werkzeug.routing import Rule

from pysmvt.config import QuickSettings

class Settings(QuickSettings):
    
    def __init__(self):
        QuickSettings.__init__(self)
        
        self.routes = ([
            Rule('/usertests/setfoo', endpoint='usertests:SetFoo'),
            Rule('/usertests/getfoo', endpoint='usertests:GetFoo'),
            Rule('/usertests/setauth', endpoint='usertests:SetAuthenticated'),
            Rule('/usertests/getauth', endpoint='usertests:GetAuthenticated'),
            Rule('/usertests/addperm', endpoint='usertests:AddPerm'),
            Rule('/usertests/getperms', endpoint='usertests:GetPerms'),
            Rule('/usertests/clear', endpoint='usertests:Clear'),
            Rule('/usertests/setmsg', endpoint='usertests:SetMessage'),
            Rule('/usertests/getmsg', endpoint='usertests:GetMessage'),
            Rule('/usertests/nomsg', endpoint='usertests:GetNoMessage'),
        ])