from blazeweb.views import View

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
        self.render_template()
