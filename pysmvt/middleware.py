from os import path
import time
from tempfile import TemporaryFile
from StringIO import StringIO
from werkzeug import EnvironHeaders, LimitedStream
from pysutils import randchars, pformat, tolist
from pysmvt import settings
from pysmvt.utils.filesystem import mkdirs

class HttpRequestLogger(object):
    """
        Logs the full HTTP request to text files for debugging purposes
        
        Note: should only be used low-request applications and/or with filters.
        
        Example (<project>/applications.py):
        
            def make_wsgi(profile='Default'):
        
                config.appinit(settingsmod, profile)
                
                app = WSGIApplication()
                
                <...snip...>
                
                app = HttpRequestLogger(app, enabled=True, path_info_filter='files/add', request_method_filter='post')
                
                return app
            
    """
    def __init__(self, application, enabled=False, path_info_filter=None, request_method_filter=None ):
        self.log_dir = path.join(settings.dirs.logs, 'http_requests')
        mkdirs(self.log_dir)
        self.application = application
        self.enabled = enabled
        self.pi_filter = path_info_filter
        self.rm_filter = request_method_filter
    
    def __call__(self, environ, start_response):
        if self.enabled:
            self.headers = EnvironHeaders(environ)
            should_log = True
            if self.pi_filter is not None and self.pi_filter not in environ['PATH_INFO']:
                should_log = False
            if self.rm_filter is not None and environ['REQUEST_METHOD'].lower() not in map(lambda x: x.lower(), tolist(self.rm_filter)):
                should_log = False
            if should_log:
                wsgi_input = self.replace_wsgi_input(environ)
                fname = '%s_%s' % (time.time(), randchars())
                fh = open(path.join(self.log_dir, fname), 'wb+')
                try:
                    fh.write(pformat(environ))
                    fh.write('\n')
                    fh.write(wsgi_input.read())
                    wsgi_input.seek(0)
                finally:
                    fh.close()
        return self.application(environ, start_response)
    
    def replace_wsgi_input(self, environ):
        content_length = self.headers.get('content-length', type=int)
        limited_stream = LimitedStream(environ['wsgi.input'], content_length)
        if content_length is not None and content_length > 1024 * 500:
            wsgi_input = TemporaryFile('wb+')
        else:
            wsgi_input = StringIO()
        wsgi_input.write(limited_stream.read())
        wsgi_input.seek(0)
        environ['wsgi.input'] = wsgi_input
        return environ['wsgi.input']