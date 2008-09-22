# -*- coding: utf-8 -*-

from pysmvt.application import request_context as rc
from werkzeug import BaseRequest, BaseResponse

class Request(BaseRequest):
    """
    Simple request subclass that allows to bind the object to the
    current context.
    """
    
    def __init__(self, environ, populate_request=True, shallow=False):
        self.bind_to_context()
        BaseRequest.__init__(self, environ, populate_request, shallow)
        
    def bind_to_context(self):
        rc.request = self


class Response(BaseResponse):
    """
    Response Object
    """
        
    default_mimetype = 'text/html'