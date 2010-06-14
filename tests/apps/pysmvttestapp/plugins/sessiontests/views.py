# -*- coding: utf-8 -*-

from pysmvt import session, user, rg
from pysmvt.views import View

class SetFoo(View):

    def default(self):
        try:
            existing = session['foo']
            raise Exception('variable "foo" existed in session')
        except KeyError:
            pass
        session['foo'] = 'bar'
        return 'foo set'

class GetFoo(View):

    def default(self):
        return session['foo']
