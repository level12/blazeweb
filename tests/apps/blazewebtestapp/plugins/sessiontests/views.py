# -*- coding: utf-8 -*-

from blazeweb.globals import user, rg
from blazeweb.views import View

class SetFoo(View):

    def default(self):
        try:
            existing = rg.session['foo']
            raise Exception('variable "foo" existed in session')
        except KeyError:
            pass
        rg.session['foo'] = 'bar'
        return 'foo set'

class GetFoo(View):

    def default(self):
        return rg.session['foo']
