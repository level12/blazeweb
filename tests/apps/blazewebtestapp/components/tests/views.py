from blazeweb.globals import rg
from blazeweb.content import getcontent
from blazeweb.utils import redirect
from blazeweb.views import View, forward, jsonify
from werkzeug.exceptions import ServiceUnavailable
from formencode.validators import UnicodeString, Int

class Rvb(View):

    def default(self):
        # this view is used as a error doc handler, so we need to set the
        # status code appropriately
        if rg.respctx.error_doc_code:
            self.status_code = rg.respctx.error_doc_code
        self.retval = 'Hello World!'

class RvbWithSnippet(View):

    def default(self):
        self.retval = getcontent('tests:HwSnippet').primary

class Get(View):

    def get(self):
        self.retval = 'Hello World!'

class Post(View):

    def post(self):
        return 'Hello World!'

class Prep(View):
    def init(self):
        self.retval = 'Hello World!'

    def default(self):
        pass

class NoActionMethod(View):
    def init(self):
        self.retval = 'Hello World!'

class DoForward(View):
    def default(self):
        forward('tests:ForwardTo')

class ForwardTo(View):
    def default(self):
        return 'forward to me'

class RaiseExc(View):
    def default(self):
        raise ValueError('exception for testing')

#class TextSnippet(TextTemplateSnippet):
#    def default(self):
#        pass
#
class Text(View):
    def default(self):
        self.render_template(default_ext='txt')

class TextWithSnippet(View):
    def default(self):
        self.assign('output',  getcontent('tests:text_snippet.txt'))
        self.render_template(default_ext='txt')

class TextWithSnippet2(View):
    def default(self):
        self.render_template(default_ext='txt')

class Html(View):
    def default(self):
        self.render_template()

class Redirect(View):
    def default(self):
        redirect('some/other/page')

class PermRedirect(View):
    def default(self):
        redirect('some/other/page', permanent=True)

class CustRedirect(View):
    def default(self):
        redirect('some/other/page', code=303)

class HttpExceptionRaise(View):
    def default(self):
        raise ServiceUnavailable()

class ForwardLoop(View):
    def default(self):
        forward('tests:ForwardLoop')

class UrlArguments(View):
    def default(self, towho='World', anum=None):
        if anum==None:
            return 'Hello %s!' % towho
        else:
            return 'Give me a name!'

class GetArguments(View):
    def init(self):
        self.add_processor('towho', UnicodeString())

    def default(self, greeting='Hello', towho='World', anum=None):
        if anum==None:
            return '%s %s!' % (greeting, towho)
        else:
            return 'Give me a name!'

class GetArguments2(View):
    def init(self):
        self.add_processor('towho', UnicodeString())
        self.add_processor('num', Int())

    def default(self, towho='World', num=None):
        if num:
            return 'Hello %s, %d!' % (towho, num)
        else:
            return 'Hello %s!' % towho

class GetArguments3(View):
    def init(self):
        self.add_processor('towho', UnicodeString())
        self.add_processor('num', Int(), show_msg=True)
        self.add_processor('num2', Int(), custom_msg='num: must be an integer')
        self.strict_args = True

    def default(self, towho='World', num=None, num2=None):
        if num:
            return 'Hello %s, %d!' % (towho, num)
        else:
            return 'Hello %s!' % towho

class RequiredGetArguments(View):
    def init(self):
        self.add_processor('towho', UnicodeString(), show_msg=True)
        self.add_processor('num', Int, required=True, show_msg=True)
        self.add_processor('num2', Int, strict=True, show_msg=True)
        self.add_processor('num3', Int, show_msg=True)

    def default(self, towho='World', num=None, num2=10, num3=10):
        if num:
            return 'Hello %s, %d %d %d!' % (towho, num, num2, num3)

class ListGetArguments(View):
    def init(self):
        self.add_processor('nums', Int(), show_msg=True, takes_list=True)

    def default(self, nums=[]):
        return str(nums)

class CustomValidator(View):
    def init(self):
        self.add_processor('num', self.validate_num)

    def default(self, num=10):
        return str(num)

    def validate_num(self, value):
        return int(value)

class BadValidator(View):
    def init(self):
        self.add_processor('num', 'notavalidator')

    def default(self, num=10):
        return num

class HtmlTemplateFileArg(View):
    def default(self):
        self.render_template('filearg.html')

class TemplateInheritance(View):
    def default(self):
        self.render_template()

class ParentTemplate(View):
    def default(self):
        self.render_template()

class ParentTemplateInheritance(View):
    def default(self):
        self.render_template()

class ModLevelPriority(View):
    def default(self):
        self.render_template()

class HtmlSnippetWithCss(View):
    def default(self):
        self.render_template()

class HtmlSnippetWithCssParent(View):
    def default(self):
        self.retval = getview('tests:HtmlSnippetWithCss')
        self.render_template()

class UserMessages(View):
    def default(self):
        if rg.respctx.error_doc_code:
            self.status_code = rg.respctx.error_doc_code
        self.render_template()

class TemplateChooser(View):
    def default(self, rtype):
        if rtype == 'endpoint':
            self.render_endpoint('app_level.html')
        if rtype == 'content':
            self.render_endpoint('tests:HwSnippet')

class JsonifyException(View):
    @jsonify
    def default(self):
        foo
