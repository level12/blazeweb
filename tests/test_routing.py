import config
import unittest

from pysmvt.routing import *
from pysmvt.exceptions import SettingsError
from pysmvttestapp.applications import make_wsgi
from werkzeug import Client, BaseResponse, create_environ

class RoutingSettings(config.Testruns):
    def __init__(self):
        config.Testruns.__init__(self)
    
        self.routing.routes.extend([
            Rule('/<file>', endpoint='static', build_only=True),
            Rule('/c/<file>', endpoint='styles', build_only=True),
            Rule('/js/<file>', endpoint='javascript', build_only=True),
            Rule('/', endpoint='mod:Index'),
            Rule('/url1', endpoint='mod:Url1'),
        ])

class Prefixsettings(RoutingSettings):
    def __init__(self):
        RoutingSettings.__init__(self)
        
        self.routing.prefix = '/prefix'

class TestRouting(unittest.TestCase):
    def setUp(self):
        self.app = config.make_console(RoutingSettings)
        self.app.start_request()
    
    def tearDown(self):
        self.app.end_request()
        self.app = None
    
    def test_routes(self):
        self.assertEqual( '/url1', url_for('mod:Url1'))
        self.assertEqual('/url1?foo=bar', url_for('mod:Url1', foo='bar'))
        self.assertEqual('http://localhost/url1', url_for('mod:Url1', True))
        self.assertEqual('/c/test.css', style_url('test.css'))
        self.assertEqual('/c/test.css', style_url('test.css', app='foo'))
        self.assertEqual('/js/test.js', js_url('test.js'))
        self.assertEqual('/js/test.js', js_url('test.js', app='foo'))
        self.assertEqual('https://localhost/url1', url_for('mod:Url1', _https=True))
        self.assertEqual('http://localhost/url1', url_for('mod:Url1', _https=False))
        
class TestRoutingSSL(unittest.TestCase):
    def setUp(self):
        self.app = config.make_console(RoutingSettings)
        env = create_environ("/test/url", "https://localhost:8080/script")
        self.app.start_request(env)
    
    def tearDown(self):
        self.app.end_request()
        self.app = None
    
    def test_routes(self):
        self.assertEqual( '/script/url1', url_for('mod:Url1'))
        self.assertEqual('/script/url1?foo=bar', url_for('mod:Url1', foo='bar'))
        self.assertEqual('https://localhost:8080/script/url1', url_for('mod:Url1', True))
        self.assertEqual('/script/c/test.css', style_url('test.css'))
        self.assertEqual('/script/c/test.css', style_url('test.css', app='foo'))
        self.assertEqual('/script/js/test.js', js_url('test.js'))
        self.assertEqual('/script/js/test.js', js_url('test.js', app='foo'))
        self.assertEqual('https://localhost:8080/script/url1', url_for('mod:Url1', _https=True))
        self.assertEqual('http://localhost:8080/script/url1', url_for('mod:Url1', _https=False))

class TestRoutingSSLCaseSensitive(unittest.TestCase):
    def setUp(self):
        self.app = config.make_console(RoutingSettings)
        env = create_environ("/test/url", "HTTPS://localhost:8080/scRipt")
        self.app.start_request(env)
    
    def tearDown(self):
        self.app.end_request()
        self.app = None
    
    def test_routes(self):
        self.assertEqual('https://localhost:8080/scRipt/url1', url_for('mod:Url1', True))
        self.assertEqual('https://localhost:8080/scRipt/url1', url_for('mod:Url1', _https=True))
        self.assertEqual('http://localhost:8080/scRipt/url1', url_for('mod:Url1', _https=False))

class TestPrefix(unittest.TestCase):
    def setUp(self):
        self.app = config.make_console(Prefixsettings)
        self.app.start_request()
    
    def tearDown(self):
        self.app.end_request()
        self.app = None
    
    def test_routes(self):
        self.assertEqual('/prefix/url1', url_for('mod:Url1'))
        self.assertEqual('/prefix/url1?foo=bar', url_for('mod:Url1', foo='bar'))
        self.assertEqual('http://localhost/prefix/url1', url_for('mod:Url1', True))
        self.assertEqual('/prefix/c/test.css', style_url('test.css'))
        self.assertEqual('/prefix/c/test.css', style_url('test.css', app='foo'))
        self.assertEqual('/prefix/js/test.js', js_url('test.js'))
        self.assertEqual('/prefix/js/test.js', js_url('test.js', app='foo'))
        self.assertEqual('https://localhost/prefix/url1', url_for('mod:Url1', _https=True))
        self.assertEqual('http://localhost/prefix/url1', url_for('mod:Url1', _https=False))

class TestCurrentUrl(unittest.TestCase):

    def setUp(self):
        self.app = make_wsgi('Testruns')
        self.client = Client(self.app, BaseResponse)

    def tearDown(self):
        self.client = None
        self.app = None

    def test_in_view(self):
        r = self.client.get('routingtests/currenturl?foo=bar')

        self.assertEqual(r.status, '200 OK')
        
        self.assertEqual(r.data, 'http://localhost/routingtests/currenturl?foo=bar')

    def test_arguments(self):
        env = create_environ("/news/list?param=foo", "http://localhost:8080/script")
        self.assertEqual('http://localhost:8080/script/news/list?param=foo', current_url(environ=env))
        self.assertEqual('http://localhost:8080/script/', current_url(environ=env, root_only=True))
        self.assertEqual('http://localhost:8080/', current_url(environ=env, host_only=True))
        self.assertEqual('http://localhost:8080/script/news/list', current_url(environ=env, strip_querystring=True))
        self.assertEqual('/script/news/list?param=foo', current_url(environ=env, strip_host=True))
        self.assertEqual('http://localhost:8080/script/news/list?param=foo', current_url(environ=env, https=False))
        self.assertEqual('http://localhost:8080/script/', current_url(environ=env, root_only=True, https=False))
        self.assertEqual('http://localhost:8080/', current_url(environ=env, host_only=True, https=False))
        self.assertEqual('http://localhost:8080/script/news/list', current_url(environ=env, strip_querystring=True, https=False))
        self.assertEqual('/script/news/list?param=foo', current_url(environ=env, strip_host=True, https=False))

        env = create_environ("/news/list?param=foo", "https://localhost:8080/script")
        self.assertEqual('https://localhost:8080/script/news/list?param=foo', current_url(environ=env))
        self.assertEqual('https://localhost:8080/script/', current_url(environ=env, root_only=True))
        self.assertEqual('https://localhost:8080/', current_url(environ=env, host_only=True))
        self.assertEqual('https://localhost:8080/script/news/list', current_url(environ=env, strip_querystring=True))
        self.assertEqual('/script/news/list?param=foo', current_url(environ=env, strip_host=True))
        self.assertEqual('https://localhost:8080/script/news/list?param=foo', current_url(environ=env, https=True))
        self.assertEqual('https://localhost:8080/script/', current_url(environ=env, root_only=True, https=True))
        self.assertEqual('https://localhost:8080/', current_url(environ=env, host_only=True, https=True))
        self.assertEqual('https://localhost:8080/script/news/list', current_url(environ=env, strip_querystring=True, https=True))
        self.assertEqual('/script/news/list?param=foo', current_url(environ=env, strip_host=True, https=True))
        self.assertEqual('/script/', current_url(root_only=True, strip_host=True, environ=env))

        env = create_environ("/news/list?param=foo", "http://localhost:8080/")
        self.assertEqual('http://localhost:8080/news/list?param=foo', current_url(environ=env))
        self.assertEqual('http://localhost:8080/', current_url(environ=env, root_only=True))
        self.assertEqual('http://localhost:8080/', current_url(environ=env, host_only=True))
        self.assertEqual('http://localhost:8080/news/list', current_url(environ=env, strip_querystring=True))
        self.assertEqual('/news/list?param=foo', current_url(environ=env, strip_host=True))
        self.assertEqual('http://localhost:8080/news/list?param=foo', current_url(environ=env, https=False))
        self.assertEqual('http://localhost:8080/', current_url(environ=env, root_only=True, https=False))
        self.assertEqual('http://localhost:8080/', current_url(environ=env, host_only=True, https=False))
        self.assertEqual('http://localhost:8080/news/list', current_url(environ=env, strip_querystring=True, https=False))
        self.assertEqual('/news/list?param=foo', current_url(environ=env, strip_host=True, https=False))
        self.assertEqual('/', current_url(root_only=True, strip_host=True, environ=env))
    
    def test_qs_replace_new(self):
        env = create_environ("/news/list?page=5&perpage=10", "http://localhost:8080/")
        self.assertEqual('http://localhost:8080/news/list?page=1&perpage=10', current_url(environ=env, qs_replace={'page':1, 'foo':'bar'}))
        self.assertEqual('http://localhost:8080/news/list?foo=bar&page=1&perpage=10', current_url(environ=env, qs_update={'page':1, 'foo':'bar'}))

if __name__ == '__main__':
    unittest.main()
