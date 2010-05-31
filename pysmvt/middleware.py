from os import path
import time
from tempfile import TemporaryFile
from StringIO import StringIO

from beaker.middleware import SessionMiddleware
from paste.registry import RegistryManager
from werkzeug import EnvironHeaders, LimitedStream, \
    SharedDataMiddleware, DebuggedApplication

from pysutils import randchars, pformat, tolist
from pysutils.datastructures import BlankObject
from pysmvt import ag, session, user, settings, rg, config
from pysmvt.utils.filesystem import mkdirs
from pysmvt.users import User

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

class RequestPrep(object):
    def __init__(self, app, ag, config_settings):
        self.application = app
        self.ag = ag
        self.settings = config_settings
    
    def __call__(self, environ, start_response):
        environ['pysmvt.middleware.RequestManager'] = True
        self.registry_setup(environ)
        self.routing_setup(environ)
        return self.application(environ, start_response)
    
    def registry_setup(self, environ):
        if environ.has_key('paste.registry'):
            environ['paste.registry'].register(settings, self.settings)
            environ['paste.registry'].register(ag, self.ag)
            if environ.has_key('beaker.session'):
                environ['paste.registry'].register(session, environ['beaker.session'])
                environ['paste.registry'].register(user, self.user_setup(environ))
            else:
                environ['paste.registry'].register(session, None)
                environ['paste.registry'].register(user, None)
            environ['paste.registry'].register(rg, BlankObject())
    
    def routing_setup(self, environ):
        rg.urladapter = ag.route_map.bind_to_environ(environ)
    
    def user_setup(self, environ):
        try:
            return environ['beaker.session'].setdefault('__pysmvt_user', User())
        except KeyError, e:
            if '__pysmvt_user' not in str(e):
                raise
            environ['beaker.session']['__pysmvt_user'] = User()
            return environ['beaker.session']['__pysmvt_user']

class ErrorDocumentsHandler(object):
    def __init__(self, app):
        self.application = app
        
    def __call__(self, environ, start_response):
        return self.application(environ, start_response)

class ExceptionHandler(object):
    def __init__(self, app):
        self.application = app
        
    def __call__(self, environ, start_response):
        return self.application(environ, start_response)

class ResponseCycleHandler(object):
    def __init__(self, app):
        self.application = app
        
    def __call__(self, environ, start_response):
        return self.application(environ, start_response)

def middleware_manager(app, ag, config_settings):
    
    app = ResponseCycleHandler(app)
    
    # serve static files from main app and supporting apps (need to reverse order b/c
    # middleware stack is run in bottom up order).  This works b/c if a
    # static file isn't found, the ShardDataMiddleware just forwards the request
    # to the next app.
    if config_settings.static_files.enabled:
        for appname in config.appslist(reverse=True):
            app_py_mod = __import__(appname)
            fs_static_path = path.join(path.dirname(app_py_mod.__file__), 'static')
            static_map = {routing.add_prefix('/') : fs_static_path}
            app = SharedDataMiddleware(app, static_map)
    
    if config_settings.exception_handling:
        app = ExceptionHandler(app)
    
    # assign request global objects, session/user, and routing
    app = RequestPrep(app, ag, config_settings)
    
    # beaker sessions
    if config_settings.beaker.enabled:
        app = SessionMiddleware(app, **dict(config_settings.beaker))
        
    # paste.registry for global object initilization
    app = RegistryManager(app)
    
    if config_settings.logs.http_requests.enabled:
        app = HttpRequestLogger(app, True,
                config_settings.logs.http_requests.filters.path_info,
                config_settings.logs.http_requests.filters.request_method)
    
    # show nice stack traces and debug output if enabled
    if settings.debugger.enabled:
        app = DebuggedApplication(app, evalex=settings.debugger.interactive)

    return app