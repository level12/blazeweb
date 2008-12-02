from urlparse import urlparse
from pysmvt import settings, rg
from werkzeug.routing import Rule, RequestRedirect
from werkzeug.exceptions import NotFound, MethodNotAllowed
from pysmvt.exceptions import SettingsError, ProgrammingError

__all__ = [
    'Rule',
    'url_for',
    'style_url',
    'js_url',
    'index_url',
    'add_prefix'
]

def url_for(endpoint, _external=False, **values):
    return rg.urladapter.build(endpoint, values, force_external=_external)

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