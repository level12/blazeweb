
from werkzeug.exceptions import HTTPException, InternalServerError

class TemplateException(HTTPException):
    code = 500
    description = '<p>A fatal error occured while trying to process a template.</p>'
    
class RedirectException(Exception):
    pass

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