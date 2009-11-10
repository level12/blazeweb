# -*- coding: utf-8 -*-

from pysmvt import rg
from werkzeug import BaseRequest, BaseResponse, ResponseStreamMixin

class Request(BaseRequest):
    """
    Simple request subclass that allows to bind the object to the
    current context.
    """
    
    def __init__(self, environ, populate_request=True, shallow=False):
        self.bind_to_context()
        BaseRequest.__init__(self, environ, populate_request, shallow)
        
    def bind_to_context(self):
        rg.request = self

    @property
    def is_xhr(self):
        rw = self.headers.get('X-Requested-With', None)
        if rw == 'XMLHttpRequest':
            return True
        return False

class Response(BaseResponse):
    """
    Response Object
    """
        
    default_mimetype = 'text/html'

class StreamResponse(Response, ResponseStreamMixin):
    """
    Response Object with a .stream method
    """
        
    default_mimetype = 'application/octet-stream'


try:
    import simplejson as json
    class JSONResponse(Response):
        
        default_mimetype = 'application/json'
        
    def _get_data(self):
        return BaseResponse.data
    def _set_data(self, data):
        BaseResponse.data = json.dumps(data)
    json_data = property(_get_data, _set_data)
    
except ImportError:
    class JSONResponse(Response):
        def __init__(self, *args, **kwargs):
            raise ImportError('simplejson package required to use JSONResponse')
        