# -*- coding: utf-8 -*-

from pysmvt.view import RespondingViewBase, SnippetViewBase, TextTemplatePage, \
    TextTemplateSnippet, HtmlTemplateSnippet, HtmlTemplatePage

class Rvb(RespondingViewBase):
    
    def default(self):
        self.retval = 'Hello app2!'


class InApp2(RespondingViewBase):
    
    def default(self):
        self.retval = 'Hello app2!'

class UnderscoreTemplates(HtmlTemplatePage):
    def default(self):
        pass