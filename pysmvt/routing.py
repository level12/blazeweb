from urlparse import urlparse
from pysmvt import settings, rg
from werkzeug import Href, MultiDict
from werkzeug.routing import Rule, RequestRedirect
from werkzeug.exceptions import NotFound, MethodNotAllowed
from werkzeug.wrappers import BaseRequest
from pysmvt.exceptions import SettingsError, ProgrammingError

__all__ = [
    'Rule',
    'url_for',
    'style_url',
    'js_url',
    'index_url',
    'add_prefix',
    'current_url'
]

def url_for(endpoint, _external=False, _https=None, **values):
    if _https is not None:
        _external = True
    url = rg.urladapter.build(endpoint, values, force_external=_external)
    if _https and url.startswith('http:'):
        url = url.replace('http:', 'https:', 1)
    elif _https == False and url.startswith('https:'):
        # need to specify _external=True for this to fire
        url = url.replace('https:', 'http:', 1)
    return url

def static_url(endpoint, file, app = None):
    """
        all this does is remove app right now, but we are anticipating:
        https://apache.rcslocal.com:8443/projects/pysmvt/ticket/40
    """
    return url_for(endpoint, file=file)

def style_url(file, app = None):
    endpoint = 'styles'
    return static_url(endpoint, file=file, app=app)

def js_url(file, app = None):
    endpoint = 'javascript'
    return static_url(endpoint, file=file, app=app)

def index_url(full=False):
    from warnings import warn
    warn(DeprecationWarning('index_url() is deprecated.  Functionality is now'
                            ' provided by current_url(root_only=True).'),
            stacklevel=2
        )
    try:
        if settings.routing.prefix:
            url = '/%s/' % settings.routing.prefix.strip('/')
        else:
            url = '/'
        
        endpoint, args = rg.urladapter.match( url )
        return url_for(endpoint, _external=full, **args)
    except NotFound:
        raise SettingsError('the index url "%s" could not be located' % url)
    except MethodNotAllowed :
        raise ProgrammingError('index_url(): MethodNotAllowed exception encountered')
    except RequestRedirect, e:
        if full:
            return e.new_url
        parts = urlparse(e.new_url)
        return parts.path.lstrip('/')

def add_prefix(path):
    if settings.routing.prefix:
        return '/%s/%s' % (settings.routing.prefix.strip('/'), path.lstrip('/'))
    return path

def current_url(root_only=False, host_only=False, strip_querystring=False,
    strip_host=False, https=None, environ=None, qs_replace=None,
    qs_update=None):
    """
    Returns strings based on the current URL.  Assume a request with path:

        /news/list?param=foo

    to an application mounted at:

        http://localhost:8080/script

    Then:
    :param root_only: set `True` if you only want the root URL.
        http://localhost:8080/script/
    :param host_only: set `True` if you only want the scheme, host, & port.
        http://localhost:8080/
    :param strip_querystring: set to `True` if you don't want the querystring.
        http://localhost:8080/script/news/list
    :param strip_host: set to `True` you want to remove the scheme, host, & port:
        /script/news/list?param=foo
    :param https: None = use schem of current environ; True = force https
        scheme; False = force http scheme.  Has no effect if strip_host = True.
    :param qs_update: a dict of key/value pairs that will be used to replace
        or add values to the current query string arguments.
    :param qs_replace: a dict of key/value pairs that will be used to replace
        values of the current query string.  Unlike qs_update, if a key is not
        present in the currenty query string, it will not be added to the
        returned url.
    :param environ: the WSGI environment to get the current URL from.  If not
        given, the environement from the current request will be used.  This
        is mostly for use in our unit tests and probably wouldn't have
        much application in normal use.
    """
    retval = ''
    if environ:
        ro = BaseRequest(environ, shallow=True)
    else:
        ro = rg.request
    
    if qs_replace or qs_update:
        strip_querystring = True
    
    if root_only:
        retval = ro.url_root
    elif host_only:
        retval = ro.host_url
    else:
        if strip_querystring:
            retval = ro.base_url
        else:
            retval = ro.url
    if strip_host:
        retval = retval.replace(ro.host_url.rstrip('/'), '', 1)
    if not strip_host and https != None:
        if https and retval.startswith('http://'):
            retval = retval.replace('http://', 'https://', 1)
        elif not https and retval.startswith('https://'):
            retval = retval.replace('https://', 'http://', 1)
    
    if qs_update or qs_replace:
        href = Href(retval, sort=True)
        args = MultiDict(ro.args)
        
        if qs_update:
            # convert to md first so that if we have lists in the kwargs, they
            # are converted appropriately
            qs_update = MultiDict(qs_update)
            
            for key, value_list in qs_update.iterlists():
                # multidicts extend, not replace, so we need
                # to get rid of the key first
                try:
                    del args[key]
                except KeyError:
                    pass
                args.setlistdefault(key, []).extend(value_list)
        
        if qs_replace:
            # convert to md first so that if we have lists in the kwargs, they
            # are converted appropriately
            qs_replace = MultiDict(qs_replace)
            
            for key, value_list in qs_replace.iterlists():
                # multidicts extend, not replace, so we need
                # to get rid of the key first
                try:
                    del args[key]
                    args.setlistdefault(key, []).extend(value_list)
                except KeyError:
                    pass
            
        return href(args)
    elif qs_update:
        href = Href(retval, sort=True)
        return href(MultiDict(querystring_new))
    return retval