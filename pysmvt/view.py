
from pysmvt.utils import reindent, auth_error, log_info, bad_request_error, fatal_error, urlslug
from pysmvt.application import request_context as rc
from pysmvt.templates import JinjaHtmlBase
from pysmvt.exceptions import ActionError, UserError
from werkzeug.wrappers import BaseResponse
from werkzeug.exceptions import InternalServerError
from werkzeug.utils import MultiDict
import formencode
from pprint import PrettyPrinter
rc.application.loader.app_names('utils', 'fatal_error', globals())

class ViewBase(object):
    """
    The base class all our views will inherit
    """
    
    def __init__(self, modulePath, endpoint, args):
        self.modulePath = modulePath
        # the view methods are responsible for filling self.retval
        # with the response string
        self.retval = ""
        # store the args MultiDict for access later
        if isinstance(args, MultiDict):
            self.args = args
        else:
            self.args = MultiDict(args)
        # the endpoint of this view
        self._endpoint = endpoint
        # the list of methods that should be called in call_methods()
        self._call_methods_stack = []
        # validators for GET arguments
        self.validators = []
        
        log_info('%s view instantiated' % self.__class__.__name__)
        
    def call_methods(self):
        
        try:
            # call prep method if it exists
            if hasattr(self, 'prep'):
                getattr(self, 'prep')()           
            
            self.args_validation()
    
            # linearize the MultiDict since most of the time we will not be
            # interested in url or GET arguments with multiple values
            # which can still be accessed if needed from self.args
            argsdict = self.args.to_dict()
            
            # loop through all the calls requested
            for call_details in self._call_methods_stack:
                if hasattr(self, call_details['method_name']):
                    if call_details['assign_args']:
                        getattr(self, call_details['method_name'])(**argsdict)
                    else:
                        getattr(self, call_details['method_name'])()

            if rc.request.method == 'GET' and hasattr(self, 'get'):
                self.get(**argsdict)
            elif rc.request.method == 'POST' and hasattr(self, 'post'):
                self.post(**argsdict)
            else:
                self.default(**argsdict)
        except UserError, e:
            rc.user.add_message('error', str(e))
            fatal_error(orig_exception=e)
        except Exception, e:
            if rc.application.settings.trap_view_exceptions:
                fatal_error(orig_exception=e)
            raise
    
    def args_validation(self):
        invalid_args = []
        
        for argname, validator, show_user_msg, msg, takes_list in self.validators:
            # get the value from the request object MultiDict
            if takes_list:
                value = rc.request.args.getlist(argname)
            else:
                value = rc.request.args.get(argname)
            
            # validate the value
            if isinstance(validator, formencode.Validator):
                try:
                    value = validator.to_python(value)
                    if value != None:
                        if isinstance(value, list):
                            self.args.setlist(argname, value)
                        else:
                            self.args[argname] = value
                except formencode.Invalid, e:
                    invalid_args.append((argname, value))
                    msg = (msg or e)
                    if show_user_msg:
                        rc.user.add_message('error', msg)
            else:
                TypeError('the validator must extend formencode.Validator')

        if len(invalid_args) > 0:
            bad_request_error('%s had bad args: %s' % (self._endpoint, invalid_args))

    def validate(self, argname, validator, show_user_msg = False, msg='', takes_list = False):
        self.validators.append((argname, validator, show_user_msg, msg, takes_list))
        
    def handle_response(self):
        raise NotImplementedError('ViewBase.handle_response() must be implemented in a subclass')
    
    def __call__(self):
        self.call_methods()
        return self.handle_response()
        
class RespondingViewBase(ViewBase):
    def __init__(self, modulePath, endpoint, args):
        ViewBase.__init__(self, modulePath, endpoint, args)
        if rc.respview is not None:
            raise InternalServerError('Responding view intialized but one already exists.'
                                      'Only one responding view is allowed per request.')
        rc.respview = self
        
    def handle_response(self):
        # @todo: we currently do redirects by returning a redirect exception
        # which inherits from BaseResponse
        if isinstance(self.retval, BaseResponse):
            rc.response = self.retval
        else:
            rc.response.data = self.retval

class HtmlPageViewBase(RespondingViewBase):
    def __init__(self, modulePath, endpoint, args):
        RespondingViewBase.__init__(self, modulePath, endpoint, args)
        self.css = []
        self.js = []
        
    def add_css(self, css):
        self.css.append(css)
    
    def add_js(self, js):
        self.js.append(js)

class SnippetViewBase(ViewBase):
    def handle_response(self):
        return self.retval
    
class HtmlSnippetViewBase(ViewBase):

    def __init__(self, modulePath, endpoint, args):
        ViewBase.__init__(self, modulePath, endpoint, args)
    
    def handle_response(self):
        #return our html
        return self.retval

class TemplateMixin(object):
    
    def init(self):
        self.assignTemplateFunctions()
        self.assignTemplateVariables()
        self.template_name = None
        
    def assignTemplateFunctions(self):
        from pysmvt.routing import style_url, index_url, url_for, js_url
        self.template.templateEnv.globals['url_for'] = url_for
        self.template.templateEnv.globals['style_url'] = style_url
        self.template.templateEnv.globals['js_url'] = js_url
        self.template.templateEnv.globals['index_url'] = index_url
        self.template.templateEnv.globals['include_css'] = self.include_css
        self.template.templateEnv.globals['include_js'] = self.include_js
        self.template.templateEnv.globals['page_css'] = self.page_css
        self.template.templateEnv.globals['page_js'] = self.page_js
        self.template.templateEnv.globals['process_view'] = self.process_view
        self.template.templateEnv.filters['urlslug'] = urlslug
        self.template.templateEnv.filters['pprint'] = self.filter_pprint
    
    def filter_pprint(self, value, indent=1, width=80, depth=None):
        return '<pre class="pretty_print">%s</pre>' % PrettyPrinter(indent, width, depth).pformat(value)
    
    def assignTemplateVariables(self):
        self.template.assign('application', rc.application)
        self.template.assign('sesuser', rc.user)
    
    def assign(self, key, value):
        self.template.assign(key, value)
    
    def include_css(self, filename=None):
        if filename == None:
            filename = self.template_name + '.css'
        contents, filepath, reloadfunc = self.template.templateEnv.loader.get_source(self.template.templateEnv, filename)
        rc.respview.add_css(contents)    
        return ''
    
    def include_js(self, filename=None):
        if filename == None:
            filename = self.template_name + '.js'
        contents, filepath, reloadfunc = self.template.templateEnv.loader.get_source(self.template.templateEnv, filename)
        rc.respview.add_js(contents)
        return ''
    
    def page_css(self, indent=8):
        #print rc.respview.css
        return reindent(''.join(rc.respview.css), indent).lstrip()
    
    def page_js(self, indent=8):
        #print rc.respview.css
        return reindent(''.join(rc.respview.js), indent).lstrip()
    
    def process_view(self, view, **kwargs):
        return rc.controller.call_view(view, kwargs)
            
    def handle_response(self):
        if self.template_name == None:
            self.template_name = self.__class__.__name__
        self.template.templateName = self.template_name
        self.retval = self.template.render()

class HtmlTemplatePage(HtmlPageViewBase, TemplateMixin):
    
    def __init__(self, modulePath, endpoint, args):
        super(HtmlTemplatePage, self).__init__(modulePath, endpoint, args)
        self.template = JinjaHtmlBase(modulePath)
        TemplateMixin.init(self)
    
    def handle_response(self):
        TemplateMixin.handle_response(self)
        super(HtmlTemplatePage, self).handle_response()

class HtmlTemplateSnippet(HtmlSnippetViewBase, TemplateMixin):
    
    def __init__(self, modulePath, endpoint, args):
        super(HtmlTemplateSnippet, self).__init__(modulePath, endpoint, args)
        self.template = JinjaHtmlBase(modulePath)
        TemplateMixin.init(self)
    
    def handle_response(self):
        TemplateMixin.handle_response(self)
        return super(HtmlTemplateSnippet, self).handle_response()