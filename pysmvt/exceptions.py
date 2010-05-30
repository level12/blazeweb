
from werkzeug.exceptions import HTTPException, InternalServerError
from werkzeug import MultiDict
from pysutils import pformat

class TemplateException(HTTPException):
    code = 500
    description = '<p>A fatal error occured while trying to process a template.</p>'

class ExceptionToClient(InternalServerError):
    pass

class Redirect(HTTPException):
    def __init__(self, location, code):
        self.code = code
        self.description = 'You are being redirected to: %s' % location
        self.location = location
        HTTPException.__init__(self)
        
    def get_headers(self, environ):
        """Get a list of headers."""
        return [('Content-Type', 'text/html'),
                ('Location', self.location)]

class Abort(HTTPException):
    def __init__(self, outputobj=None, code=200):
        from pysmvt.utils import werkzeug_multi_dict_conv
        from pysmvt.utils.html import escape
        self.code = code
        if isinstance(outputobj, MultiDict):
            outputobj = werkzeug_multi_dict_conv(outputobj)
        self.description = "<pre>%s</pre>" % escape(pformat(outputobj)) if outputobj else ''
        HTTPException.__init__(self)

class ForwardException(Exception):
    pass

class ActionError(Exception):
    def __init__(self, type, description = ''):
        self.type = type
        self.description = description

class UserError(Exception):
    """ called when the system can not proceed b/c of a user error """
    pass

class ProgrammingError(Exception):
    """
        raised when a programming error is detected
    """
    pass

class SettingsError(Exception):
    """
        raised when a settings error is detected
    """
    pass

class ViewCallStackAbort(Exception):
    """
        used to stop the views from running through all the methods in the
        call stack. Don't use directly, use the send_response() method on the
        view instead.
    """