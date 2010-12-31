from blazeweb.globals import settings, user, rg
from blazeweb.utils import abort
from blazeweb.views import View, asview
from blazeweb.wrappers import Response

class AppLevelView(View):
    def init(self):
        self.expect_getargs('v2')

    def default(self, v1=None, v2=None):
        return 'alv: %s, %s' % (v1, v2)

class Index(View):
    def default(self, tname):
        self.assign('a', 1)
        if tname != 'index':
            self.render_template(tname)
        user.foo = 'bar'
        rg.session['foo'] = 'bar2'
        self.render_template()

class Abort(View):
    def default(self, tname):
        if tname == 'int':
            abort(400)
        if tname == 'callable':
            abort(Response('test Response'))
        if tname == 'str':
            abort('test & str')
        if tname == 'other':
            abort({'foo':'bar', 'b&z': 1})
        if tname == 'dabort':
            dabort([])
        assert False

class EventTest(View):
    def default(self):
        return 'foo'
