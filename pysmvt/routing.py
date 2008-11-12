from pysmvt.application import request_context as rc
from pysmvt import settings
from werkzeug.routing import Rule

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

def style_url(file, app = None):
    endpoint = 'styles'
    return url_for(endpoint, file=file, app=app)

def js_url(file, app = None):
    endpoint = 'javascript'
    return url_for(endpoint, file=file, app=app)

def index_url(url = None):
    if settings.routing.prefix:
       return '/%s/' % settings.routing.prefix.strip('/')
    return '/'

def add_prefix(path):
    if settings.routing.prefix:
        return '/%s/%s' % (settings.routing.prefix.strip('/'), path.lstrip('/'))
    return path