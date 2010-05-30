# -*- coding: utf-8 -*-

from pysmvt import rg
from werkzeug import BaseRequest as WerkBaseRequest, BaseResponse, ResponseStreamMixin, MultiDict, \
    EnvironBuilder
from pysmvt.utils import registry_has_object

class BaseRequest(WerkBaseRequest):
    # we want mutable request objects
    parameter_storage_class = MultiDict

class Request(BaseRequest):
    """
    Simple request subclass that allows to bind the object to the
    current context.
    """
    
    @classmethod
    def from_values(cls, data, method='POST', bind_to_context=False, **kwargs):
        env = EnvironBuilder(method=method, data=data, **kwargs).get_environ()
        return cls(env, bind_to_context=bind_to_context)

    def replace_http_args(self, method='POST', *args, **kwargs):
        """
            using the same parameters as from_values(),
            creates a new BaseRequest from args and kwargs and then replaces
            .args, .form, and .files on the current request object with the
            values from the new request.
        """
        nreq = BaseRequest.from_values(method=method, *args, **kwargs)
        self.args = nreq.args
        self.form = nreq.form
        self.files = nreq.files

    def __init__(self, environ, populate_request=True, shallow=False, bind_to_context=True):
        if bind_to_context:
            self.bind_to_context()
        BaseRequest.__init__(self, environ, populate_request, shallow)
        
    def bind_to_context(self):
        if registry_has_object(rg):
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
        
        def _get_jsondata(self):
            return self.data
        def _set_jsondata(self, data):
            self.data = json.dumps(data)
        json_data = property(_get_jsondata, _set_jsondata)
    
except ImportError:
    class JSONResponse(Response):
        def __init__(self, *args, **kwargs):
            raise ImportError('simplejson package required to use JSONResponse')
        