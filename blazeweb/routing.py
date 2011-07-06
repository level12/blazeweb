from urlparse import urlparse

from blazeweb.globals import settings, rg
from blazeweb.utils import registry_has_object
from werkzeug import Href, MultiDict
from werkzeug.routing import Rule, RequestRedirect
from werkzeug.exceptions import NotFound, MethodNotAllowed
from werkzeug.wrappers import BaseRequest
from blazeweb.exceptions import SettingsError, ProgrammingError

__all__ = [
    'Rule',
    'url_for',
    'static_url',
    'current_url',
    'prefix_relative_url',
    'abs_static_url',
]

def prefix_relative_url(url):
    """
        If the url given is an absolute url of any of the following forms:

            http(s)://example.com/the-page
            /the-page
            /

        then the url will be returned as-is.  But if it is a relative url:

            the-page

        or an empty string "", then it will be prefixed with forward slash (/)
        as well as the script-name of the current environment if applicable.

        Note: this function checks for the presence of the current environment
        in a safe way and can therefore be used both inside and outside of a
        request context.

    """
    if url.startswith('http') or url.startswith('/'):
        return url
    if registry_has_object(rg):
        script_name = rg.request.script_root
        if script_name:
            return '/%s/%s' % (script_name.lstrip('/'), url)
    return '/%s' % url

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

def static_url(path):
    """
        Adds the conifgured "static" files prefix to the relative URL passed in.

        NOTE: abs_static_url() will probably be more useful
    """
    return '%s/%s' % (settings.routing.static_prefix.rstrip('/'), path.lstrip('/'))

def abs_static_url(path):
    """
        Same as prefix_relative_url(static_url(path))
    """
    return prefix_relative_url(static_url(path))

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
