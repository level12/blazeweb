
from werkzeug.exceptions import HTTPException

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