import logging
from os import path
from StringIO import StringIO
from tempfile import TemporaryFile
import time

from beaker.middleware import SessionMiddleware
from blazeutils import randchars, pformat, tolist
from paste.registry import RegistryManager
from werkzeug import EnvironHeaders, LimitedStream, \
    SharedDataMiddleware, DebuggedApplication

from blazeweb import routing
from blazeweb.hierarchy import list_component_mappings, findfile, FileNotFound
from blazeweb.globals import settings, ag
from blazeweb.utils.filesystem import mkdirs

log = logging.getLogger(__name__)

class HttpRequestLogger(object):
    """
        Logs the full HTTP request to text files for debugging purposes

        Note: should only be used low-request applications and/or with filters.

        Example (<project>/applications.py):

            def make_wsgi(profile='Default'):

                config.appinit(settingsmod, profile)

                app = WSGIApp()

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

class StaticFileServer(SharedDataMiddleware):
    """
        Serves static files based on hierarchy structure
    """
    def __init__(self, app, **kwargs):
        exports = {'/' + routing.static_url('/') : ''}
        SharedDataMiddleware.__init__(self, app, exports, **kwargs)

    def debug(self, pathpart, msg):
        log.debug('StaticFileServer 404 (%s): %s', pathpart, msg)

    def get_directory_loader(self, directory):
        def loader(pathpart):
            if pathpart is None:
                self.debug(pathpart, 'pathpart is None')
                return None, None
            if not pathpart.count('/'):
                self.debug(pathpart, 'pathpart had no slashes')
                return None, None
            type, locpath = pathpart.split('/', 1)
            if not locpath:
                self.debug(pathpart, 'pathpart had type, but not locpath')
                return None, None
            if type not in ('app', 'component'):
                self.debug(pathpart, 'type was not "app" or "component"')
                return None, None
            if type == 'component':
                if not locpath.count('/'):
                    self.debug(pathpart, 'component type, but locpath had no slashes')
                    return None, None
                component, locpath = locpath.split('/', 1)
            # look in the static directory
            locpath = 'static/' + locpath
            if type == 'app':
                endpoint = locpath
            else:
                endpoint = '%s:%s' % (component, locpath)
            try:
                fpath = findfile(endpoint)
                return path.basename(fpath), self._opener(fpath)
            except FileNotFound:
                self.debug(pathpart, 'endpoint "%s" not found' % endpoint)
                return None, None
        return loader

def static_files(app):
    settings = ag.app.settings

    if settings.static_files.enabled:
        # serve static files from static directory (e.g. after copying
        # from the source packages; use static-copy command for that)
        if settings.static_files.location  == 'static':
            exported_dirs = {'/' + routing.static_url('/') : settings.dirs.static}
            return SharedDataMiddleware(app, exported_dirs)
        # serve static files from source packages based on hierarchy rules
        return StaticFileServer(app)
    return app

class RegistrySetup(object):
    """
        Sets up the paste.registry objects and application level
        globals for each request.
    """
    def __init__(self, wsgiapp, bwapp):
        self.wsgiapp = wsgiapp
        self.bwapp = bwapp

    def __call__(self, environ, start_response):
        environ['paste.registry'].register(settings, self.bwapp.settings)
        environ['paste.registry'].register(ag, self.bwapp.ag)
        return self.wsgiapp(environ, start_response)

def full_wsgi_stack(app):
    """
        returns the WSGIApp wrapped in common middleware
    """

    settings = ag.app.settings

    if settings.beaker.enabled:
        app = SessionMiddleware(app, **dict(settings.beaker))

    app = static_files(app)

    app = minimal_wsgi_stack(app)

    # show nice stack traces and debug output if enabled
    if settings.debugger.enabled:
        app = DebuggedApplication(app, evalex=settings.debugger.interactive)

    # log http requests, use sparingly on production servers
    if settings.logs.http_requests.enabled:
        app = HttpRequestLogger(app, True,
                settings.logs.http_requests.filters.path_info,
                settings.logs.http_requests.filters.request_method)

    return app

def minimal_wsgi_stack(app):
    """
        returns a WSGI application wrapped in minimal middleware, mostly useful
        for internal testing
    """
    app = RegistrySetup(app, ag.app)
    app = RegistryManager(app)
    return app
