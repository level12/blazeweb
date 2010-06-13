from pysmvt import forward, redirect
from pysmvt.views import View

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
        if tname:
            self.template_name = tname
        self.assign('a', 1)
        self.render_template()

class FakeView(object):
    pass

class InAppHasPriority(object):
    pass

class OnlyForCache(object):
    pass
