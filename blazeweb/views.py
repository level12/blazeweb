import logging
from new import classobj

from decorator import decorator
import formencode
from blazeutils.sentinels import NotGiven
from blazeutils.helpers import tolist
from blazeutils.strings import case_cw2us
from werkzeug import MultiDict, validate_arguments, ArgumentValidationError, \
    abort
from werkzeug.exceptions import BadRequest
from werkzeug.routing import Rule

from blazeweb.globals import ag, rg, user, settings
from blazeweb import routing
from blazeutils.jsonh import jsonmod, assert_have_json
from blazeweb.content import getcontent, Content
from blazeweb.hierarchy import listapps, split_endpoint
from blazeweb.exceptions import ProgrammingError
from blazeweb.utils import registry_has_object, werkzeug_multi_dict_conv
from blazeweb.wrappers import Response

log = logging.getLogger(__name__)

__all__ = (
    'View',
    'SecureView',
    'asview',
    'jsonify'
)
###
### internal stuff
###

def _calc_component_name(module):
    """ calculates the component a view is in """
    parts = module.split('.')
    if len(parts) == 2:
        """ its in a package, that means the first part is the package name """
        if parts[0] in listapps():
            # its app level
            return None
        # it should be a component
        return settings.component_packages[parts[0]]
    # its an internal component
    return parts[2]

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

class _ViewCallStackAbort(Exception):
    """
        used to stop the views from running through all the methods in the
        call stack. Don't use directly, use the send_response() method on the
        view instead.
    """
###
### primary View objects
###

class View(object):
    """
    The base class all our views will inherit
    """

    # map HTTP REQUEST_METHOD to a method on our class
    http_method_map = {
        # legacy methods didn't use http_ prefix
        'get': 'get',
        'post': 'post',

        # in hindsight, with this many methods, prefixing with http_ seems best.
        'head': 'http_head',
        'put': 'http_put',
        'delete': 'http_delete',
        'options': 'http_options',
        'connect': 'http_connect',
        'patch': 'http_patch',

        # XHR: special type of request used in JavaScript
        '_xhr_': 'xhr',

        # this is the "fallback" method, it will be called if no specific
        # methods on the class match.
        '_default_': 'default',
    }

    def __init__(self, urlargs, endpoint):
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
        # the default Response object to be used when creating a response
        self.response_class = Response
        # mime/type of the response
        self.mimetype = 'text/html'
        # store endpoint for later use
        self.endpoint = endpoint
        # store the component name for later use
        component, _ = split_endpoint(endpoint)
        self._component_name = component

        log.debug('%s view instantiated', self.__class__.__name__)

        # setup our method call stack
        self.init_call_methods()

    ###
    ### method stack helpers
    ###
    def init_call_methods(self):
        # use this method if you need to do view setup, but need getargs to do it
        # and therefore can not do the setup in init()
        self.add_call_method('setup_view')

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
            show_msg=False, custom_msg=None, pass_as=None ):
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
            pass_as = When the argname is not a valid python variable (e.g.
                ?listvalues[]=1&listvalues[]=2), then set pass_as to a string
                that corresponds to the variable name that should be used
                when passing this value to the action methods.
        """
        if not self.urlargs.has_key(argname):
            self.expect_getargs(argname)
        if custom_msg:
            show_msg = True
        if required:
            if not processor:
                processor = formencode.validators.NotEmpty()
            strict = True
        if processor:
            for proc in tolist(processor):
                if not formencode.is_validator(proc):
                    if not hasattr(proc, '__call__'):
                        raise TypeError('processor must be a Formencode validator or a callable')
                    proc = _ProcessorWrapper(to_python=proc)
                self._processors.append((argname, proc, required, takes_list,
                    list_item_invalidates, strict, show_msg, custom_msg, pass_as))
        else:
            self._processors.append((argname, None, required, takes_list,
                list_item_invalidates, strict, show_msg, custom_msg, pass_as))

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
        except _ViewCallStackAbort:
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
        log.debug('calling args: %s' % self.calling_args)

    def process_args(self):
        had_strict_arg_failure = False
        for argname, processor, required, takes_list, list_item_invalidates, \
                strict, show_msg, custom_msg, pass_as in self._processors:
            is_invalid = False
            pass_as = pass_as or argname
            argval = self.calling_args.get(argname, None)
            try:
                if isinstance(argval, list):
                    if takes_list == False:
                        raise formencode.Invalid('multiple values not allowed', argval, None)
                    if takes_list is None:
                        self.calling_args[pass_as] = argval = argval[0]
                elif takes_list:
                    self.calling_args[pass_as] = argval = tolist(argval)
                if pass_as != argname:
                    # catches a couple cases where a replacement doesn't
                    # already happen above
                    self.calling_args[pass_as] = argval
                    # delete the old value if it exists
                    if argname in self.calling_args:
                        del self.calling_args[argname]
                if processor:
                    if takes_list:
                        processor = formencode.ForEach(processor)
                    try:
                        if required:
                            processor = formencode.All(formencode.validators.NotEmpty, processor)
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
                    self.calling_args[pass_as] = processed_val
            except formencode.Invalid, e:
                is_invalid = True
                if self.strict_args or strict:
                    had_strict_arg_failure = True
                self.invalid_arg_keys.append(argname)
                if show_msg:
                    invalid_msg = '%s: %s' % (argname, custom_msg or str(e))
                    user.add_message('error', invalid_msg)
            try:
                if is_invalid or self.calling_args[pass_as] is None or self.calling_args[pass_as] == '':
                    del self.calling_args[pass_as]
            except KeyError:
                pass
        if len(self.invalid_arg_keys) > 0:
            log.debug('%s had bad args: %s', self.__class__.__name__, self.invalid_arg_keys)
        if had_strict_arg_failure:
            raise BadRequest('strict arg failure w/ invalid keys: %s' % self.invalid_arg_keys)

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
        http_method = rg.request.method.lower()
        method_name = None

        # handle XHR (Ajax) requests
        if rg.request.is_xhr:
            method_name = self.http_method_map['_xhr_']
            # if the method isn't present, treat it as a non-xhr request
            if method_name and not hasattr(self, method_name):
                method_name = None

        # handle based on HTTP request method type
        if not method_name and http_method in self.http_method_map:
            method_name = self.http_method_map[http_method]

        # if there wasn't a method name found or the method name doesn't exist
        # as a method, then try the default handler
        if method_name is None or not hasattr(self, method_name):
            method_name = self.http_method_map.get('_default_')
            if method_name is None or not hasattr(self, method_name):
                # default fallback failed, we can't handle this request method
                abort(405)

        # call the method that responds to this request method type
        retval = self._call_with_expected_args(getattr(self, method_name))

        # we allow the views to work on self.retval directly, but if the
        # action method returns a non-None value, it takes precedence
        if retval is not None:
            self.retval = retval

    def _call_with_expected_args(self, method, method_is_bound=True):
        log.debug('calling w/ expected: %s %s' % (method, self.calling_args))
        """ handle argument conversion to what the method accepts """
        try:
            # validate_arguments is made for a function, not a class method
            # so we need to "trick" it by sending self here, but then
            # removing it before the bound method is called below
            pos_args = (self,) if method_is_bound else tuple()
            args, kwargs = validate_arguments(method, pos_args , self.calling_args.copy())
        except ArgumentValidationError, e:
            log.error('arg validation failed: %s, %s, %s, %s', method, e.missing, e.extra, e.extra_positional)
            raise BadRequest('The browser failed to transmit all '
                             'the data expected.')
        if method_is_bound:
            # remove "self" from args since its a bound method
            args = args[1:]
        return method(*args, **kwargs)

    def handle_response(self):
        # nothing returned is fine, I guess
        if self.retval is None or self.retval is NotGiven:
            self.retval = u''
        # is the return value a Content instance?
        if isinstance(self.retval, Content):
            c = self.retval
            return self.create_response(c.primary, mimetype=c.primary_type)
        # if the retval is a string, add it as the response data
        if isinstance(self.retval, basestring):
            return self.create_response(self.retval)
        # if its callable, assume it is a WSGI application and return it
        # directly
        if hasattr(self.retval, '__call__'):
            return self.retval
        # convert it to a string and send as the response
        return self.create_response(str(self.retval))

    def render_template(self, filename=None, default_ext='html', send_response=True):
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
                # templates.  If the view is component level, then the search is
                # done in the compstack for that component.
                self.render_template('some_file.html')

            Calling render_template() will setup the Response object based on
            the content and type of the template.  If send_response is True
            (default), then the response will be sent immediately.  If False,
            render_template() will return the Content object.  In either case,
            self.retval will be set to the Content object.
        """
        if not filename:
            # the filename must have an extension, that is how
            # getcontent() knows we are looking for a file and not a Content
            # instance.
            filename = '%s.%s' % (case_cw2us(self.__class__.__name__), default_ext)
        endpoint = filename
        if self._component_name:
            endpoint = '%s:%s' % (self._component_name, endpoint)
        return self.render_endpoint(endpoint, send_response)

    def render_endpoint(self, endpoint, send_response=True):
        """
            Render a template or Content object by endpoint:

            # look for a template file by endpoint, useful if you need a
            # template from another component:
            self.render_endpoint('othercomponent:some_template.html')

            # or if the view is component level and a template from the main
            # application is needed.
            self.render_endpoint('app_level.html')

            # a Content object can also be rendered by omitting an extension:
            self.render_endpoint('mycomponent:SomeContent')
        """
        c = getcontent(endpoint, **self.template_vars)
        self.retval = c
        if send_response:
            self.send_response()
        return c

    def render_json(self, data, has_error=0, add_user_messages=True, indent=2,
                    send_response=True, extra_context=None):
        """
            Will send data as a json string with the appopriate mime-type
            as the response.  Status indicators as well as user messages are
            also sent.

        """
        assert_have_json()
        user_messages = []
        if add_user_messages:
            for msg in user.get_messages():
                user_messages.append({'severity':msg.severity, 'text': msg.text})

        data_with_context = {
            'error': has_error,
            'data': data,
            'messages': user_messages
            }
        if extra_context:
            data_with_context.update(extra_context)
        jsonstr = jsonmod.dumps(data_with_context, indent=indent)
        self.mimetype = 'application/json'
        self.retval = jsonstr
        if send_response:
            self.send_response()
        return jsonstr

    def create_response(self, response, status=None, mimetype=None):
        if status is None:
            status = self.status_code
        if mimetype is None:
            mimetype = self.mimetype
        return self.response_class(response, status=status, mimetype=mimetype)

    def assign(self, name, value):
        self.template_vars[name] = value

    def send_response(self):
        """
            Can be used during "processing" to abort the call stack process
            and immediately return the response.
        """
        raise _ViewCallStackAbort

class SecureView(View):
    def __init__(self, urlargs, endpoint):
        View.__init__(self, urlargs, endpoint)
        # we can skip auth if needed
        self.allow_anonymous = False
        # if False, the user is required to be authenticated only
        self.check_authorization = True
        # do we know who the user is?
        self.is_authenticated = False
        # do they have permission to use the resource they are trying to use?
        self.is_authorized = False
        # if check_authorization is True, require the user to have at least
        # one of these permission
        self.require_any = []
        # if check_authorization is True, require the user to have all of the
        # following permissions
        self.require_all = []

    def init_call_methods(self):
        """
            note that we do not call the parent as we don't want setup_view()
            in the callstack.  Use auth_pre instead.  Using this naming
            convention can help remind the developer that auth_pre() is being
            called before auth methods and hopefully avoid security issues
            by forgetting that setup_view() comes before authorization
        """

        ###
        ### setup the call stack methods
        ###
        # auth_pre is used to do pre_auth setup when argument values
        # are needed (and can therefore not be done in init()
        self.add_call_method('auth_pre')
        # auth calculate sets our security attributes (is_auth*) based on the
        # require_* attributes and the current user.  You can override this
        # if you have custom auth requirements.
        self.add_call_method('auth_calculate', required=True)
        # auth_verify checks our security attributes and calls
        # not_authenticated() or not_authorized() if necessary.  This should
        # not be overriden, override auth_calculate instead and set the
        # security attributes accordingly.
        self.add_call_method('auth_verify', required=True, takes_args=False)
        # for view setup after the user has been authorized
        self.add_call_method('auth_post')

    def auth_calculate(self, **kwargs):
        if not user.is_authenticated:
            return
        self.is_authenticated = True

        self.is_authorized = self.auth_calculate_any_all(self.require_any, self.require_all)

    def auth_calculate_any_all(self, any, all):
        # if require_all is given and there are any failures, deny authorization
        for perm in tolist(all):
            if not user.has_perm(perm):
                return False
        # if there was at least one value for require_all and not values for
        # require any, then the user is authorized
        if all and not any:
            return True
        # at this point, require_all passed or was empty and require_any has
        # at least one value, so this is the final check to determine
        # authorization
        if user.has_any_perm(any):
            return True
        return False

    def auth_verify(self):
        if self.allow_anonymous:
            return
        if not self.is_authenticated:
            self.not_authenticated()
        if not self.check_authorization:
            return
        if not self.is_authorized:
            self.not_authorized()

    def not_authenticated(self):
        abort(401)

    def not_authorized(self):
        abort(403)

###
### functions and classes related to processing functions as views
###

# views modules will get reloaded by hierarchy.visitmods and there is no sense
# recreating the class definition each time
CLASS_CACHE = {}

def asview(rule=None, **options):
    """
        A decorator to use a function as a View
    """
    def decorate(f):
        lrule = rule
        fname = f.__name__
        getargs = options.pop('getargs', [])
        component_prefix = _calc_component_name(f.__module__)

        # calculate the endpoint
        endpoint = fname
        if component_prefix is not None:
            endpoint = '%s:%s' % (component_prefix, endpoint)

        # setup the routing
        if lrule is None:
            lrule = '/%s' % fname
        log.debug('@asview adding route "%s" to endpoint "%s"', lrule, endpoint)
        ag.route_map.add(Rule(lrule, endpoint=endpoint), **options)

        # cache key for this object
        cachekey = '%s:%s' % (f.__module__, fname)

        # create the class that will handle this function if it doesn't already
        # exist in the cache
        if cachekey not in CLASS_CACHE:
            fvh = classobj(fname, (_AsViewHandler, ), {})
            fvh.__module__ = f.__module__

            # make the getargs available
            fvh._asview_getargs = tolist(getargs)

            # store this class object in the cache so we don't have to
            # recreate next time
            CLASS_CACHE[cachekey] = fvh
        else:
             fvh = CLASS_CACHE[cachekey]

        # assign the default method.  This can't be cached because on a reload
        # of the views module, the first decorated function will become
        # None.  So we have to recreate the defmethod wrapper with the
        # function object that is being created/recreated and decorated.
        def defmethod(self):
            return self._call_with_expected_args(f, method_is_bound=False)
        fvh.default = defmethod

        # return the class instead of the function
        return fvh
    return decorate

class _AsViewHandler(View):
    def __init__(self, urlargs, endpoint):
        View.__init__(self, urlargs, endpoint)
        self.expect_getargs(*self._asview_getargs)
###
### other internal views
###

class _RouteToTemplate(View):
    """
        used by the Application when the route contains a template endpoint
        instead of a View endpoint.
    """
    def default(self, **kwargs):
        self.template_vars = kwargs
        self.render_endpoint(self.endpoint)

###
### json related
###

def json_exception_handler(e):
    data_with_context = {
        'error': 1,
        'data': None,
        'messages': [{'error':'exception encountered, see logs for details'}]
        }
    jsonstr = jsonmod.dumps(data_with_context)
    return Response(jsonstr, status=500, mimetype='application/json')

@decorator
def jsonify(f, self, *args, **kwargs):
    """
        use on a function in the view callback; it will take the returned data
        and call render_json() with the data.  Will also handle exceptions.
    """
    rg.exception_handler = json_exception_handler
    data = f(self, *args, **kwargs)
    self.render_json(data)

###
### view forwarding
###

class _Forward(Exception):
    def __init__(self, endpoint, args):
        Exception.__init__(self)
        self.forward_endpoint = endpoint
        self.forward_args = args

def forward(endpoint, **kwargs):
    raise _Forward(endpoint, kwargs)
