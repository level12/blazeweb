# -*- coding: utf-8 -*-

from pysmvt import getview, redirect, forward
from pysmvt.view import RespondingViewBase, SnippetViewBase, TextTemplatePage, \
    TextTemplateSnippet, HtmlTemplateSnippet, HtmlTemplatePage, HtmlPageViewBase
from werkzeug.exceptions import ServiceUnavailable
from formencode.validators import UnicodeString, Int

class Rvb(RespondingViewBase):
    
    def default(self):
        self.retval = 'Hello World!'

class HwSnippet(SnippetViewBase):
    def default(self):
        self.retval = 'Hello World!'

class RvbWithSnippet(RespondingViewBase):
    
    def default(self):
        self.retval = getview('tests:HwSnippet')

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
        return getview('tests:Rvb')

class DoForward(RespondingViewBase):
    def default(self):
        forward('tests:ForwardTo')

class ForwardTo(RespondingViewBase):
    def default(self):
        return 'forward to me'

class BadForward(RespondingViewBase):
    def default(self):
        forward('tests:HwSnippet')

class TextSnippet(TextTemplateSnippet):
    def default(self):
        pass

class Text(TextTemplatePage):
    def default(self):
        pass

class TextWithSnippet(TextTemplatePage):
    def default(self):
        self.assign('output',  getview('tests:TextSnippet'))

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
        redirect('some/other/page')

class PermRedirect(RespondingViewBase):
    def default(self):
        redirect('some/other/page', permanent=True)

class CustRedirect(RespondingViewBase):
    def default(self):
        redirect('some/other/page', code=303)

class HttpExceptionRaise(RespondingViewBase):
    def default(self):
        raise ServiceUnavailable()

class ForwardLoop(RespondingViewBase):
    def default(self):
        forward('tests:ForwardLoop')

class UrlArguments(RespondingViewBase):
    def default(self, towho='World', anum=None):
        if anum==None:
            return 'Hello %s!' % towho
        else:
            return 'Give me a name!'

class GetArguments(RespondingViewBase):
    def prep(self):
        self.validate('towho', UnicodeString())

    def default(self, greeting='Hello', towho='World', anum=None):
        if anum==None:
            return '%s %s!' % (greeting, towho)
        else:
            return 'Give me a name!'


class GetArguments2(RespondingViewBase):
    def prep(self):
        self.validate('towho', UnicodeString())
        self.validate('num', Int())

    def default(self, towho='World', num=None):
        if num:
            return 'Hello %s, %d!' % (towho, num)
        else:
            return 'Hello %s!' % towho

class GetArguments3(RespondingViewBase):
    def prep(self):
        self.validate('towho', UnicodeString())
        self.validate('num', Int(), True)
        self.validate('num2', Int(), 'num: must be an integer')
        self.strict_args = True

    def default(self, towho='World', num=None, num2=None):
        if num:
            return 'Hello %s, %d!' % (towho, num)
        else:
            return 'Hello %s!' % towho

class RequiredGetArguments(RespondingViewBase):
    def prep(self):
        self.validate('towho', UnicodeString(), msg=True)
        self.validate('num', Int, required=True, msg=True)
        self.validate('num2', Int, strict=True, msg=True)
        self.validate('num3', Int, msg=True)

    def default(self, towho='World', num=None, num2=10, num3=10):
        if num:
            return 'Hello %s, %d %d %d!' % (towho, num, num2, num3)
        
class ListGetArguments(RespondingViewBase):
    def prep(self):
        self.validate('nums', Int(), msg=True, takes_list=True)

    def default(self, nums=[]):
        return str(nums)
        
class CustomValidator(RespondingViewBase):
    def prep(self):
        self.validate('num', self.validate_num)

    def default(self, num=10):
        return num
    
    def validate_num(self, value):
        return int(value)
        
class BadValidator(RespondingViewBase):
    def prep(self):
        self.validate('num', 'notavalidator')

    def default(self, num=10):
        return num

class HtmlTemplateError1(HtmlTemplatePage):
    def default(self):
        self.template_name = 'test'
        self.template_file = 'test'

class HtmlTemplateFileArg(HtmlTemplatePage):
    def default(self):
        self.template_file = 'filearg.html'
        
class TemplateInheritance(HtmlTemplatePage):
    def default(self):
        pass
    
class ParentTemplate(HtmlTemplatePage):
    def default(self):
        pass
    
class ParentTemplateInheritance(HtmlTemplatePage):
    def default(self):
        pass
    
class ModLevelPriority(HtmlTemplatePage):
    def default(self):
        pass
    
class HtmlTemplateFileArgCss(HtmlTemplatePage):
    def default(self):
        self.template_file = 'fileargcss.html'

class HtmlSnippetWithCss(HtmlTemplateSnippet):
    def default(self):
        pass
    
class HtmlSnippetWithCssParent(HtmlPageViewBase):
    def default(self):
        self.retval = getview('tests:HtmlSnippetWithCss')