import logging

import formencode
from pysutils.sentinels import NotGiven
from pysutils.helpers import tolist
from pysutils.strings import case_cw2us
from werkzeug import MultiDict, validate_arguments, ArgumentValidationError, \
    abort
from werkzeug.exceptions import BadRequest
from werkzeug.routing import Rule

from pysmvt import ag, rg, user
from pysmvt import routing
from pysmvt.content import getcontent
from pysmvt.exceptions import ViewCallStackAbort, ProgrammingError
from pysmvt.utils import registry_has_object, werkzeug_multi_dict_conv
from pysmvt.wrappers import Response

log = logging.getLogger(__name__)

class _ProcessorWrapper(formencode.validators.Wrapper):
    """
        Only catch ValueError and TypeError, otherwise debugging can become
        a real pain.
    """
    def wrap(self, func):
        if not func:
            return None
        def result(value, state, func=func):
            try:
                return func(value)
            except (ValueError, TypeError), e:
                raise formencode.Invalid(str(e), {}, value, state)
        return result

class View(object):
    """
    The base class all our views will inherit
    """

    def __init__(self, urlargs):
        # the view methods are responsible for filling self.retval1
        # with the response string or returning the value
        self.retval = NotGiven
        # store the args dictionary from URL matching
        self.urlargs = urlargs
        # the list of methods that should be called in call_methods()
        self._cm_stack = []
        # processors for call stack arguments
        self._processors = []
        # calling_arg keys that had validation errors
        self.invalid_arg_keys = []
        # should we abort if the wrong GET args are sent?  This can be set
        # on individual processors with add_arg_processor(), but can
        # also be set for the whole view.
        self.strict_args = False
        # names of GET arguments that should be "melded" with the routing
        # arguments
        self.expected_get_args = []
        # holds the variables that will be sent to the template when
        # rendering
        self.template_vars = {}
        # the name of the template file relative to the location of the View
        # status code for the response
        self.status_code = 200

        log.debug('%s view instantiated', self.__class__.__name__)

        # setup our method call stack
        self.init_call_methods()

    ###
    ### method stack helpers
    ###
    def init_call_methods(self):
        self.add_call_method('init_response', True, False)

    def add_call_method(self, name, required=False, takes_args=True):
        self._cm_stack.append((name, required, takes_args))

    def insert_call_method(self, name, position, target, required=False, takes_args=True):
        target_pos = None
        for index, stackvals in enumerate(self._cm_stack):
            if stackvals[0] == target:
                target_pos = index
        if target_pos is None:
            raise ValueError('target "%s" was not found in the callstack' % target)
        if position not in ('before', 'after'):
            raise ValueError('position "%s" not valid; should be "before" or "after"' % position)
        if position == 'before':
            before = self._cm_stack[:target_pos]
            after = self._cm_stack[target_pos:]
        else:
            before = self._cm_stack[:target_pos+1]
            after = self._cm_stack[target_pos+1:]
        before.append((name, required, takes_args))
        self._cm_stack = before + after

    ###
    ### arg helpers
    ###
    def expect_getargs(self, *args):
        """
            The arguments passed to this method should be strings that
            correspond to the keys of rg.request.args that you want included
            in your calling arguments.  Example:

            Example for route: /myview?bar=baz

            class MyView(View):
                def default(self, bar=None):
                    assert bar is None

            class MyView(View):
                def init(self):
                    self.expect_getargs('bar')

                def default(self, bar=None):
                    assert bar == u'baz'
        """
        self.expected_get_args.extend(args)

    def add_processor(self, argname, processor=None, required=None,
            takes_list = None, list_item_invalidates=False, strict=False,
            show_msg=False, custom_msg=None ):
        """
            Sets up filtering & validation on the calling_args to be used before
            any methods in the call stack are called. The default arguments will
            cause an invalid argument to be ignored silently. However, you can
            also setup the validation process to show the user error messages
            and/or raise a 400 Bad Request.

            argname = the key that corresponds to the argument you want to
                validate.  If this key isn't found as a URL argument, it is
                assumed that it is a get argument and expect_getargs(argname)
                is called.
            processor = a callable which takes the arg value to validate as its
                single argument.  Should raise ValueError if the value is
                invalid.  It may also be a Formencode validator.  The processor
                should also return the value to use as the calling arg.  If
                validation fails and strict is not True, then the value is set
                to None.
            required = requires the argument to be present and to have a non-None
                value.  Does not alter the value.  Since the default
                behavior is to ignore a value when validation has failed, which
                results in a None value being set, it only makes sense to use
                required when strict should be True.  Therefore, strict is set
                to true implicitely when using require.
            takes_list = if True, validates multiple values and ensures that
                the calling arg associated with argname is a list even if only
                one item was sent.  If None or False, only the first value
                will be validated and the calling arg associated with argname
                will not be a list, even if multiple values are present in
                calling_args. If None, having more than one value for argname is
                not considered a validation error. If False, it is considered a
                validation error.
            strict = If validation fails, raise a 400 Bad Request exception.
                The exception is raised after all validation has taken place, so
                user messages will still be set for all errors if applicable.
                Therefore, if your error doc handler shows user messages, the
                user can still be informed of the reason why they received
                the error.
            list_item_invalidates = When set to False and a list item fails
                validation, it is simply ignored. If strict_list == True, then a
                single validation error is considered a validation error for the
                whole argument, causing the value to be set to [].
            show_msg = should the user be shown an error message if validation
                on this argument fails?  If custom_msg == True, show_msg also
                gets set to True.
            custom_msg = A custom error msg to show the user if validation
                fails.  If not given, and if validator is a Formencode
                validator, then the message will be take from the formencode
                validator.  If not given and the validator is a callable, then
                the message will be taken from the ValueError exception that
                is raised.  If given, show_msg is implicitly set to True.
        """
        if not self.urlargs.has_key(argname):
            self.expect_getargs(argname)
        if custom_msg:
            show_msg = True
        if processor:
            if not formencode.is_validator(processor):
                if not hasattr(processor, '__call__'):
                    raise TypeError('processor must be a Formencode validator or a callable')
                processor = _ProcessorWrapper(to_python=processor)
        if required:
            if not processor:
                processor = formencode.validators.NotEmpty()
            strict = True
        self._processors.append((argname, processor, required, takes_list,
            list_item_invalidates, strict, show_msg, custom_msg))

    ###
    ### methods in the default call stack
    ###
    def init_response(self):
        rg.respctx.response = Response()

    ###
    ### methods related to processing the view
    ###
    def process(self):
        """
            called to get the view's response
        """
        try:
            # call prep method if it exists.  This is not part of the call stack
            # because it allows the view instance to customize the call stack
            # before it starts being used in the loop below
            if hasattr(self, 'init'):
                getattr(self, 'init')()

            # turn URL args and GET args into a single MultiDict and store
            # on self.calling_args
            self.process_calling_args()

            # validate/process self.calling_args
            self.process_args()

            # call each method in the call stack
            self.process_cm_stack()

            # call the action method
            self.process_action_method()
        except ViewCallStackAbort:
            pass
        return self.handle_response()

    def process_calling_args(self):
        # start with GET arguments that are expected
        args = MultiDict()
        if self.expected_get_args:
            for k in rg.request.args.iterkeys():
                if k in self.expected_get_args:
                    args.setlist(k, rg.request.args.getlist(k))

        # add URL arguments, replacing GET arguments if they are there.  URL
        # arguments get precedence and we don't want to just .update()
        # because that would allow arbitrary get arguments to affect the
        # values of the URL arguments
        for k,v in self.urlargs.iteritems():
            args[k] = v

        # trim down to a real dictionary.
        self.calling_args = werkzeug_multi_dict_conv(args)

    def process_args(self):
        had_strict_arg_failure = False

        for argname, processor, required, takes_list, list_item_invalidates, \
                strict, show_msg, custom_msg in self._processors:
            is_invalid = False
            argval = self.calling_args.get(argname, None)
            try:
                if isinstance(argval, list):
                    if takes_list == False:
                        raise formencode.Invalid('multiple values not allowed', argval, None)
                    if takes_list is None:
                        self.calling_args[argname] = argval = argval[0]
                elif takes_list:
                    self.calling_args[argname] = argval = tolist(argval)
                if processor:
                    if takes_list:
                        processor = formencode.ForEach(processor)
                    try:
                        processor.not_empty = required
                        processed_val = processor.to_python(argval)
                    except formencode.Invalid, e:
                        """ do a second round of processing for list values """
                        if not takes_list or not e.error_list or list_item_invalidates:
                            raise
                        """ only remove the bad values, keep the good ones """
                        new_list = []
                        for index, error in enumerate(e.error_list):
                            if error is None:
                                new_list.append(argval[index])
                        # revalidate for conversion and required
                        processed_val = processor.to_python(new_list)
                    self.calling_args[argname] = processed_val
            except formencode.Invalid, e:
                is_invalid = True
                if self.strict_args or strict:
                    had_strict_arg_failure = True
                self.invalid_arg_keys.append(argname)
                if show_msg:
                    invalid_msg = '%s: %s' % (argname, custom_msg or str(e))
                    user.add_message('error', invalid_msg)
            try:
                if is_invalid or self.calling_args[argname] is None or self.calling_args[argname] == '':
                    del self.calling_args[argname]
            except KeyError:
                pass
        if len(self.invalid_arg_keys) > 0:
            log.debug('%s had bad args: %s', self.__class__.__name__, self.invalid_arg_keys)
        if had_strict_arg_failure:
            raise BadRequest()

    def process_cm_stack(self):
        # loop through all the calls requested
        for method_name, required, takes_args in self._cm_stack:
            if not hasattr(self, method_name) and not required:
                continue
            methodobj = getattr(self, method_name)
            if not takes_args:
                methodobj()
            else:
                self._call_with_expected_args(methodobj)

    def process_action_method(self):
        # now call our "action" methods, only one of these methods will be
        # called depending on the type of request and the attributes
        # available on the view
        if rg.request.is_xhr and hasattr(self, 'xhr'):
            retval = self._call_with_expected_args(self.xhr)
        elif rg.request.method == 'GET' and hasattr(self, 'get'):
            retval = self._call_with_expected_args(self.get)
        elif rg.request.method == 'POST' and hasattr(self, 'post'):
            retval = self._call_with_expected_args(self.post)
        else:
            try:
                retval = self._call_with_expected_args(self.default)
            except AttributeError, e:
                if "'%s' object has no attribute 'default'" % self.__class__.__name__ in str(e):
                    raise ProgrammingError('there were no "action" methods on the view class "%s".  Expecting get(), post(), or default()' % self.__class__.__name__)
                raise

        # we allow the views to work on self.retval directly, so if it has
        # been used, we do not replace it with the returned value.  If it
        # hasn't been used, then we replace it with what was returned
        # above
        if self.retval is NotGiven:
            self.retval = retval

    def _call_with_expected_args(self, method, method_is_bound=True):
        """ handle argument conversion to what the method accepts """
        try:
            # validate_arguments is made for a function, not a class method
            # so we need to "trick" it by sending self here, but then
            # removing it before the bound method is called below
            pos_args = (self,) if method_is_bound else tuple()
            args, kwargs = validate_arguments(method, pos_args , self.calling_args)
        except ArgumentValidationError, e:
            log.error('arg validation failed: %s, %s, %s, %s', method, e.missing, e.extra, e.extra_positional)
            raise BadRequest('The browser failed to transmit all '
                             'the data expected.')
        if method_is_bound:
            # remove "self" from args since its a bound method
            args = args[1:]
        return method(*args, **kwargs)

    def handle_response(self):
        # if retval is None, assume respctx.response was altered directly
        if self.retval is None or self.retval is NotGiven:
            return rg.respctx.response
        # if the retval is a string, add it as the response data
        if isinstance(self.retval, basestring):
            rg.respctx.response.data = self.retval
            return rg.respctx.response
        # if its callable, assume it is a WSGI application and return it
        # directly
        if hasattr(self.retval, '__call__'):
            return self.retval
        raise TypeError('View "%s" returned a value with an unexpected type: %s' % (self.__class__.__name__, type(self.retval)))

    def render_template(self, filename=None, endpoint=None, default_ext='html', send_response=True):
        """
            Render a template:

                # use a template based on the view's name.  If the view is named
                # "MyView" then the template should be named 'my_view.html'.
                self.render_template()

                # you can also set a different extension if the template is
                # named like the view, but is not html:
                self.render_template(default_ext='txt')

                # look for a template file with the name given.  If the view
                # is app level, then the search is done in the appstack's
                # templates.  If the view is plugin level, then the search is
                # done in the plugstack for that plugin.
                self.render_template('some_file.html')

                # look for a template file by endpoint, useful if you need a
                # template from another plugin:
                self.render_template(endpoint='otherplugin:some_template.html')

                # or if the view is plugin level and a template from the main
                # application is needed.
                self.render_template(endpoint='app_level.html')

            Calling render_template() will setup the Response object based on
            the content and type of the template.  If send_response is True
            (default), then the response will be sent immediately.  If False,
            render_template() will return the content of the template.
        """
        if filename and endpoint:
            raise ProgrammingError('only one of filename or endpoint can be used, not both')
        if not endpoint:
            if not filename:
                # the filename must have an extension, that is how
                # getcontent() knows we are looking for a file and not a Content
                # instance.
                filename = '%s.%s' % (case_cw2us(self.__class__.__name__), default_ext)
            if rg.respctx.current_plugin:
                endpoint = '%s:%s' % (rg.respctx.current_plugin, filename)
            else:
                endpoint = filename
        c = getcontent(endpoint, **self.template_vars)
        rg.respctx.response = Response(c.primary, status=self.status_code, mimetype=c.primary_type)
        if send_response:
            self.send_response()
        return c.primary

    def assign(self, name, value):
        self.template_vars[name] = value

    def send_response(self):
        """
            Can be used during "processing" to abort the call stack process
            and immediately return the response.
        """
        raise ViewCallStackAbort

###
### functions and classes related to processing functions as views
###
def asview(rule=None, **options):
    def decorator(f):
        lrule = rule
        fname = f.__name__
        if lrule is None:
            lrule = '/%s' % fname
        lrule = routing.add_prefix(lrule)
        getargs = options.pop('getargs', [])
        ag.view_functions[fname] = f, getargs
        endpoint = '__viewfuncs__:%s' % fname
        log.debug('@asview adding route "%s" to endpoint "%s"', lrule, endpoint)
        ag.route_map.add(Rule(lrule, endpoint=endpoint), **options)
        return f
    return decorator

class FunctionViewHandler(View):
    def __init__(self, endpoint, urlargs):
        fname = endpoint.split(':')[1]
        func, expected_get_args = ag.view_functions[fname]
        self.func = func
        View.__init__(self, urlargs)
        self.expected_get_args = expected_get_args

    def default(self):
        return self._call_with_expected_args(self.func, method_is_bound=False)
