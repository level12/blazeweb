from pysmvt.views import View

class AppLevelView(View):
    def init(self):
        self.expect_getargs('v2')

    def default(self, v1=None, v2=None):
        return 'alv: %s, %s' % (v1, v2)

class Index(View):
    def default(self, tname):
        if tname != 'index':
            self.template_name = tname
        self.assign('a', 1)
        self.render_template()
