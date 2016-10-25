import werkzeug as wz

from blazeutils.jsonh import jsonmod, assert_have_json
from blazeweb.globals import rg
from blazeweb.utils import registry_has_object

class BaseRequest(wz.Request):
    # we want mutable request objects
    parameter_storage_class = wz.MultiDict

class Request(BaseRequest):
    """
    Simple request subclass that allows to bind the object to the
    current context.
    """

    @classmethod
    def from_values(cls, data, method='POST', bind_to_context=False, **kwargs):
        env = wz.EnvironBuilder(method=method, data=data, **kwargs).get_environ()
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

    @wz.cached_property
    def json(self):
        """If the mimetype is `application/json` this will contain the
        parsed JSON data.
        """
        assert_have_json()
        if self.mimetype.endswith(('+json', '/json')):
            return jsonmod.loads(unicode(self.data, self.charset))

class Response(wz.Response):
    """
    Response Object
    """

    default_mimetype = 'text/html'

class StreamResponse(wz.Response):
    """
    Response Object with a .stream method
    """

    default_mimetype = 'application/octet-stream'


class FileResponse(wz.Response):
    """
        Uses werkzeug.wrap_file and direct_passthrough on the response
    """

    def __init__(self, fileobj=None, status=None, headers=None, mimetype=None, content_type=None,
                 buffer_size=8192):
        fw = wz.wrap_file(rg.environ, fileobj, buffer_size)
        wz.Response.__init__(self, fw, status=status, headers=headers, mimetype=mimetype,
                             content_type=content_type, direct_passthrough=True)
