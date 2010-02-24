from decorator import decorator
from os import path
from traceback import format_exc
import logging
from pysmvt import settings, user, ag, _getview, rg, appimportauto
from pysmvt.utils import reindent, auth_error, bad_request_error, \
    fatal_error, urlslug, markdown
from pysmvt.utils.html import strip_tags
from pysmvt.templates import JinjaHtmlBase, JinjaBase
from pysmvt.exceptions import ActionError, UserError, ProgrammingError, \
    ViewCallStackAbort
from pysmvt.wrappers import Response, JSONResponse
from werkzeug.wrappers import BaseResponse
from werkzeug.exceptions import InternalServerError, BadRequest
from werkzeug.utils import MultiDict
import formencode
from pprint import PrettyPrinter
from pysutils import NotGiven, moneyfmt, safe_strftime

log = logging.getLogger(__name__)

# @@todo: this is a **really** bad way to do this
try: 
    appimportauto('utils', 'fatal_error')
except ImportError, e:
    if 'cannot import "utils" with attribute "fatal_error"' not in str(e):
        raise
    from pysmvt.utils import fatal_error

class ViewBase(object):
    """
    The base class all our views will inherit
    """
    
    def __init__(self, modulePath, endpoint, args):
        self.modulePath = modulePath
        # the view methods are responsible for filling self.retval
        # with the response string or returning the value
        self.retval = NotGiven
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
        # should we abort if the wrong GET args are sent?
        self.strict_args = False
        
        log.debug('%s view instantiated', self.__class__.__name__)
        
    def call_methods(self):

        # call prep method if it exists
        if hasattr(self, 'prep'):
            getattr(self, 'prep')()           
        
        self.args_validation()

        # linearize the MultiDict so that we can pass it into the functions
        # as keywords
        argsdict = self.args.to_dict()
        
        # loop through all the calls requested
        for call_details in self._call_methods_stack:
            if hasattr(self, call_details['method_name']):
                if call_details['assign_args']:
                    getattr(self, call_details['method_name'])(**argsdict)
                else:
                    getattr(self, call_details['method_name'])()
        
        if rg.request.is_xhr and hasattr(self, 'xhr'):
            retval = self.xhr(**argsdict)
        elif rg.request.method == 'GET' and hasattr(self, 'get'):
            retval = self.get(**argsdict)
        elif rg.request.method == 'POST' and hasattr(self, 'post'):
            retval = self.post(**argsdict)
        else:
            try:
                retval = self.default(**argsdict)
            except AttributeError, e:
                if "'%s' object has no attribute 'default'" % self.__class__.__name__ in str(e):
                    raise ProgrammingError('there were no "action" methods on the view class "%s".  Expecting get(), post(), or default()' % self._endpoint)
                else:
                    raise
            
        # we allow the views to work on self.retval directly, so if it has
        # been used, we do not replace it with the returned value.  If it
        # hasn't been used, then we replace it with what was returned
        # above
        if self.retval is NotGiven:
            self.retval = retval
    
    def args_validation(self):
        invalid_args = []
        
        for argname, validator, show_msg, msg, takes_list, strict, required in self.validators:

            # validate the value
            if formencode.is_validator(validator):
                try:
                    # get the value from the request object MultiDict
                    if takes_list:
                        value = rg.request.args.getlist(argname)
                        value = [validator.to_python(v) for v in value]
                    else:
                        value = rg.request.args.get(argname)
                        value = validator.to_python(value)
                    if value or value == 0:
                        self.args[argname] = value
                    else:
                        if required:
                            #print '%s %s' % (argname, value)
                            raise formencode.Invalid('argument required', value, None)
                except formencode.Invalid, e:
                    if strict:
                        self.strict_args = True
                    invalid_args.append((argname, value))
                    if not msg:
                        msg = '%s: %s' % (argname, e)
                    if show_msg:
                        user.add_message('error', msg)
            else:
                raise TypeError('the validator must extend formencode.Validator')

        if len(invalid_args) > 0:
            log.debug('%s had bad args: %s', self._endpoint, invalid_args)
            if self.strict_args:
                raise BadRequest()

    def validate(self, argname, validator, msg=False, strict=False, required=False, takes_list = False):
        if msg:
            show_msg = True
        else:
            show_msg = False
        if msg == True:
            msg = None
        if required:
            strict = True
        if not formencode.is_validator(validator):
            if callable(validator):
                validator = formencode.validators.Wrapper(to_python=validator)
            else:
                raise TypeError('validator must be a Formencode validator or a callable')
            
        self.validators.append((argname, validator, show_msg, msg, takes_list, strict, required))
        
    def handle_response(self):
        raise NotImplementedError('ViewBase.handle_response() must be implemented in a subclass')
    
    def __call__(self):
        try:
            self.call_methods()
        except ViewCallStackAbort:
            pass
        return self.handle_response()
    
    def send_response(self):
        """
            Can be used in a method in the call stack to skip the rest of the
            methods in the stack and return the response immediately.
        """
        raise ViewCallStackAbort
        
class RespondingViewBase(ViewBase):
    def __init__(self, modulePath, endpoint, args):
        ViewBase.__init__(self, modulePath, endpoint, args)
        if hasattr(rg, 'respview'):
            raise ProgrammingError('Responding view (%s) intialized but one already exists (%s).  '
                                      'Only one responding view is allowed per request.' % (endpoint, rg.respview._endpoint))
        rg.respview = self
        self._init_response()
        
    def _init_response(self):
        self.response = Response()
        
    def handle_response(self):
        if isinstance(self.retval, BaseResponse):
            return self.retval
        else:
            self.response.data = self.retval
            return self.response

class AjaxRespondingView(RespondingViewBase):
    def _init_response(self):
        self.response = JSONResponse()

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

class TemplateMixin(object):
    
    def init(self):
        self.assignTemplateFunctions()
        self.assignTemplateVariables()
        self.template_name = None
        self.template_file = None
        
    def assignTemplateFunctions(self):
        from pysmvt.routing import style_url, index_url, url_for, js_url, current_url
        self.template.templateEnv.globals['url_for'] = url_for
        self.template.templateEnv.globals['style_url'] = style_url
        self.template.templateEnv.globals['js_url'] = js_url
        self.template.templateEnv.globals['index_url'] = index_url
        self.template.templateEnv.globals['current_url'] = current_url
        self.template.templateEnv.globals['include_css'] = self.include_css
        self.template.templateEnv.globals['include_js'] = self.include_js
        self.template.templateEnv.globals['page_css'] = self.page_css
        self.template.templateEnv.globals['page_js'] = self.page_js
        self.template.templateEnv.globals['process_view'] = self.process_view
        self.template.templateEnv.filters['urlslug'] = urlslug
        self.template.templateEnv.filters['pprint'] = self.filter_pprint
        self.template.templateEnv.filters['markdown'] = markdown
        self.template.templateEnv.filters['strip_tags'] = strip_tags
        self.template.templateEnv.filters['moneyfmt'] = moneyfmt
        self.template.templateEnv.filters['datefmt'] = safe_strftime
    
    def filter_pprint(self, value, indent=1, width=80, depth=None):
        toprint = PrettyPrinter(indent, width, depth).pformat(value)
        toprint = self.template.templateEnv.filters['e'](toprint)
        return '<pre class="pretty_print">%s</pre>' % toprint
    
    def assignTemplateVariables(self):
        self.template.assign('settings', settings)
        self.template.assign('sesuser', user)
    
    def assign(self, key, value):
        self.template.assign(key, value)
    
    def include_css(self, filename=None):
        if filename == None:
            filename = self.template_name + '.css'
        contents, filepath, reloadfunc = self.template.templateEnv.loader.get_source(self.template.templateEnv, filename)
        rg.respview.add_css(contents)    
        return ''
    
    def include_js(self, filename=None):
        if filename == None:
            filename = self.template_name + '.js'
        contents, filepath, reloadfunc = self.template.templateEnv.loader.get_source(self.template.templateEnv, filename)
        rg.respview.add_js(contents)
        return ''
    
    def page_css(self, indent=8):
        #print rg.respview.css
        return reindent(''.join(rg.respview.css), indent).lstrip()
    
    def page_js(self, indent=8):
        #print rg.respview.css
        return reindent(''.join(rg.respview.js), indent).lstrip()
    
    def process_view(self, view, **kwargs):
        return _getview(view, kwargs, 'template')
            
    def handle_response(self):
        if self.template_name and self.template_file:
            raise ProgrammingError("a view can only set template_name or template_file, not both")
        if self.template_name == None:
            self.template_name = self.__class__.__name__
        if self.template_file:
            name, ext = path.splitext(self.template_file)
            self.template.tpl_extension = ext.lstrip('.')
            self.template_name = name
        # need to set this as it affects the default names for including
        # css and js
        self.template.templateName = self.template_name
        self.retval = self.template.render()

class HtmlTemplatePage(HtmlPageViewBase, TemplateMixin):
    
    def __init__(self, modulePath, endpoint, args):
        super(HtmlTemplatePage, self).__init__(modulePath, endpoint, args)
        self.template = JinjaHtmlBase(endpoint)
        TemplateMixin.init(self)
    
    def handle_response(self):
        TemplateMixin.handle_response(self)
        return super(HtmlTemplatePage, self).handle_response()

class HtmlTemplateSnippet(SnippetViewBase, TemplateMixin):
    
    def __init__(self, modulePath, endpoint, args):
        super(HtmlTemplateSnippet, self).__init__(modulePath, endpoint, args)
        self.template = JinjaHtmlBase(endpoint)
        TemplateMixin.init(self)
    
    def handle_response(self):
        TemplateMixin.handle_response(self)
        return super(HtmlTemplateSnippet, self).handle_response()

class TextTemplatePage(RespondingViewBase, TemplateMixin):
    
    def __init__(self, modulePath, endpoint, args):
        super(TextTemplatePage, self).__init__(modulePath, endpoint, args)
        self.template = JinjaBase(endpoint)
        self.template.tpl_extension = 'txt'
        TemplateMixin.init(self)
            
    def _init_response(self):
        self.response = Response(mimetype='text/plain')
        
    def handle_response(self):
        TemplateMixin.handle_response(self)
        return super(TextTemplatePage, self).handle_response()

class TextTemplateSnippet(SnippetViewBase, TemplateMixin):
    
    def __init__(self, modulePath, endpoint, args):
        super(TextTemplateSnippet, self).__init__(modulePath, endpoint, args)
        self.template = JinjaBase(endpoint)
        self.template.tpl_extension = 'txt'
        TemplateMixin.init(self)
    
    def handle_response(self):
        TemplateMixin.handle_response(self)
        return super(TextTemplateSnippet, self).handle_response()

@decorator
def jsonify(f, self, *args, **kwargs):
    def new_handle_response():
        jresp = JSONResponse()
        retval = {}
        try:
            retval['data'] = f(self, *args, **kwargs)
            retval['error'] = 0
        except Exception, e:
            retval['error'] = 1
            log.exception('error calling jsonified function %s, %s, %s', f, args, kwargs)
            retval['data'] = ''
            user.add_message('error', 'internal error encountered, exception logged')
        retval['messages'] = []
        for msg in user.get_messages():
            retval['messages'].append({'severity':msg.severity, 'text': msg.text})
        jresp.json_data = retval
        return jresp
    self.handle_response = new_handle_response