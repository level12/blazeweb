# -*- coding: utf-8 -*-

from pysmvt.application import request_context as rc
from pysmvt.view import RespondingViewBase, SnippetViewBase, TextTemplatePage, \
    TextTemplateSnippet, HtmlTemplateSnippet, HtmlTemplatePage
from werkzeug.exceptions import ServiceUnavailable

class Rvb(RespondingViewBase):
    
    def default(self):
        self.retval = 'Hello World!'

class HwSnippet(SnippetViewBase):
    def default(self):
        self.retval = 'Hello World!'

class RvbWithSnippet(RespondingViewBase):
    
    def default(self):
        self.retval = rc.controller.call_view('tests:HwSnippet')

class Get(RespondingViewBase):
    
    def get(self):
        self.retval = 'Hello World!'

class Post(RespondingViewBase):
    
    def post(self):
        return 'Hello World!'

class Prep(RespondingViewBase):
    def prep(self):
        self.retval = 'Hello World!'
        
    def default(self):
        pass

class NoActionMethod(RespondingViewBase):
    def prep(self):
        self.retval = 'Hello World!'

class TwoRespondingViews(RespondingViewBase):
    
    def default(self):
        return rc.controller.call_view('tests:Rvb')

class DoForward(RespondingViewBase):
    def default(self):
        rc.controller.forward('tests:ForwardTo')

class ForwardTo(RespondingViewBase):
    def default(self):
        return 'forward to me'

class BadForward(RespondingViewBase):
    def default(self):
        rc.controller.forward('tests:HwSnippet')

class TextSnippet(TextTemplateSnippet):
    def default(self):
        pass

class Text(TextTemplatePage):
    def default(self):
        pass

class TextWithSnippet(TextTemplatePage):
    def default(self):
        self.assign('output',  rc.controller.call_view('tests:TextSnippet'))

class TextWithSnippet2(TextTemplatePage):
    def default(self):
        pass

class HtmlSnippet(HtmlTemplateSnippet):
    def default(self):
        pass

class Html(HtmlTemplatePage):
    def default(self):
        pass

class HtmlCssJs(HtmlTemplatePage):
    def default(self):
        pass
    
class Redirect(RespondingViewBase):
    def default(self):
        rc.controller.redirect('some/other/page')

class PermRedirect(RespondingViewBase):
    def default(self):
        rc.controller.redirect('some/other/page', permanent=True)

class CustRedirect(RespondingViewBase):
    def default(self):
        rc.controller.redirect('some/other/page', code=303)

class HttpExceptionRaise(RespondingViewBase):
    def default(self):
        raise ServiceUnavailable()

class ForwardLoop(RespondingViewBase):
    def default(self):
        rc.controller.forward('tests:ForwardLoop')

#class TextWithSnippet(TextTemplatePage):
#    def default(self):
#        self.assign('output',  rc.controller.call_view('tests:TextSnippet'))
#
#class TextWithSnippet2(TextTemplatePage):
#    def default(self):
#        pass