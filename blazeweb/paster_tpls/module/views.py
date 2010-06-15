from pysmvt import appimportauto
from pysmvt.views import View

class Index(HtmlTemplatePage):
    def default(self):
        self.render_template()
