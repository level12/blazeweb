from werkzeug.exceptions import HTTPException, InternalServerError
from werkzeug import MultiDict
from blazeutils import pformat

class Redirect(Exception):
    def __init__(self, response):
        self.response = response

class Forward(Exception):
    def __init__(self, endpoint, args):
        Exception.__init__(self)
        self.forward_endpoint = endpoint
        self.forward_args = args

class Abort(HTTPException):
    def __init__(self, outputobj=None, code=200):
        from blazeweb.utils import werkzeug_multi_dict_conv
        from blazeweb.utils.html import escape
        self.code = code
        if isinstance(outputobj, MultiDict):
            outputobj = werkzeug_multi_dict_conv(outputobj)
        self.description = "<pre>%s</pre>" % escape(pformat(outputobj)) if outputobj else ''
        HTTPException.__init__(self)

class ProgrammingError(Exception):
    """
        Raised when an API is not used correctly and the exception does
        not fit any of the builtin exceptions
    """

class SettingsError(Exception):
    """
        raised when a settings error is detected
    """
