from pysmvt.application import request_context as rc

def url_for(endpoint, _external=False, **values):
    return rc.controller.urlAdapter.build(endpoint, values, force_external=_external)

def style_url(file, app = None):
    endpoint = 'styles'
    return url_for(endpoint, file=file, app=app)

def js_url(file, app = None):
    endpoint = 'javascript'
    return url_for(endpoint, file=file, app=app)

def index_url(url = None):
    from pysmvt.exceptions import TemplateException
    from werkzeug.exceptions import NotFound, MethodNotAllowed
    from werkzeug.routing import RequestRedirect
    
    try:
        if url == None :
            try:
                if len(rc.application.settings.route_prefix) > 1:
                   url = '/%s/' % (rc.application.settings.route_prefix.strip('/'), )
                else:
                    raise AttributeError
            except AttributeError:
                url = '/'
        
        endpoint, args = rc.controller.urlAdapter.match( url )
        return url_for(endpoint, args)
    except NotFound:
        raise TemplateException('index_url(): the index url "%s" could not be located' % (url, ))
    except MethodNotAllowed:
        raise TemplateException('index_url(): MethodNotAllowed exception encountered')
    except RequestRedirect, rr:
        from urlparse import urlparse
        path_part = urlparse(rr.new_url)[2]
        if path_part == url :
            raise TemplateException('index_url(): redirect loop encountered with url "%s"' % (url, ))
        return index_url( path_part )

def add_prefix(path):
    try:
        if len(rc.application.settings.route_prefix) > 1:
           path = '/%s/%s' % (rc.application.settings.route_prefix.strip('/'), path.lstrip('/'))
        else:
            raise AttributeError
    except AttributeError:
        pass
    return path