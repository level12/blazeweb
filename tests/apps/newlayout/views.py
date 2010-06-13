from pysmvt.views import View

class AppLevelView(View):
    def init(self):
        self.expect_getargs('v2')

    def default(self, v1=None, v2=None):
        return 'alv: %s, %s' % (v1, v2)
