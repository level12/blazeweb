# -*- coding: utf-8 -*-

from blazeweb.views import View

class Rvb(View):
    def default(self):
        self.retval = 'Hello app2!'

class InApp2(View):

    def default(self):
        self.retval = 'Hello app2!'

class UnderscoreTemplates(View):
    def default(self):
        self.render_template()
