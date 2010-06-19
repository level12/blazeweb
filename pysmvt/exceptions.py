from werkzeug.exceptions import HTTPException, InternalServerError
from werkzeug import MultiDict
from pysutils import pformat

class Redirect(Exception):
    def __init__(self, response):
        self.response = response

class Forward(Exception):
    def __init__(self, endpoint, args):
        Exception.__init__(self)
        self.forward_endpoint = endpoint
        self.forward_args = args

class ProgrammingError(Exception):
    """
        Raised when an API is not used correctly and the exception does
        not fit any of the builtin exceptions
    """

class SettingsError(Exception):
    """
        raised when a settings error is detected
    """
