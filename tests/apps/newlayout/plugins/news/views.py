from blazeweb.globals import rg
from blazeweb.utils import redirect
from blazeweb.views import View, asview, forward

class Index(View):
    def init(self):
        self.expect_getargs('sendby')

    def default(self, sendby=None):
        if sendby == 'forward':
            forward('AppLevelView')
            assert False
        if sendby == 'redirect':
            redirect('/applevelview/foo')
            assert False
        if sendby == 'rdp':
            redirect('/applevelview/foo', permanent=True)
        if sendby == '303':
            redirect('/applevelview/foo', code=303)
        return 'news index'

class ForwardWithArgs(View):
    def default(self, sendby=None):
        forward('AppLevelView', v1='a', v2='b')

class Template(View):
    def init(self):
        self.expect_getargs('tname')

    def default(self, tname=None):
        self.assign('a', 1)
        if tname:
            self.render_template(tname)
        self.render_template()

class TestRequestSetupAttr(View):
    def default(self, sendby=None):
        return rg.testattr


class FakeView(object):
    pass

class InAppHasPriority(object):
    pass

class OnlyForCache(object):
    pass
