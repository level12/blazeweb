# -*- coding: utf-8 -*-

from pysmvt.application import request_context as rc
from pysmvt.view import RespondingViewBase, SnippetViewBase

class Rvb(RespondingViewBase):
    
    def default(self):
        self.retval = 'Hello World!'

class HwSnippet(SnippetViewBase):
    def default(self):
        self.retval = 'Hello World!'

class RvbWithSnippet(RespondingViewBase):
    
    def default(self):
        self.retval = rc.controller.call_view('tests:HwSnippet')