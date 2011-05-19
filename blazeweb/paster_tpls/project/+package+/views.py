from blazeweb.views import View

class Index(View):
    def default(self):
        self.render_template()
