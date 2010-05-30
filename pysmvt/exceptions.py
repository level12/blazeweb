
from werkzeug.exceptions import HTTPException, InternalServerError

class TemplateException(HTTPException):
    code = 500
    description = '<p>A fatal error occured while trying to process a template.</p>'
    
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