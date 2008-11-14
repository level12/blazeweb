import config
import unittest

from pysmvt.application import Application
import pysmvt.config
from pysmvt.routing import *

class RoutingSettings(config.Testruns):
    def __init__(self):
        config.Testruns.__init__(self)
        
        self.routing.routes.extend([
            Rule('/', endpoint='mod:Index'),
            Rule('/url1', endpoint='mod:Url1'),
        ])

class Prefixsettings(RoutingSettings):
    def __init__(self):
        RoutingSettings.__init__(self)
        
        self.routing.prefix = '/prefix'

class Noindex(RoutingSettings):
    def __init__(self):
        RoutingSettings.__init__(self)
        
        self.routing.routes = [
            Rule('/url1', endpoint='mod:Url1'),
        ]

class TestRouting(unittest.TestCase):
    def setUp(self):
        pysmvt.config.appinit(__import__(__name__), 'RoutingSettings')
        self.app = Application()
        self.app.startrequest()
    
    def tearDown(self):
        self.app.endrequest()
        self.app = None
    
    def test_routes(self):
        self.assertEqual( '/url1', url_for('mod:Url1'))
        self.assertEqual('/url1?foo=bar', url_for('mod:Url1', foo='bar'))
        self.assertEqual('http://localhost/url1', url_for('mod:Url1', True))
        self.assertEqual('/static/c/test.css', style_url('test.css'))
        self.assertEqual('/foo/static/c/test.css', style_url('test.css', app='foo'))
        self.assertEqual('/static/js/test.js', js_url('test.js'))
        self.assertEqual('/foo/static/js/test.js', js_url('test.js', app='foo'))
        self.assertEqual('/', index_url())

class TestPrefix(unittest.TestCase):
    def setUp(self):
        pysmvt.config.appinit(__import__(__name__), 'Prefixsettings')
        self.app = Application()
        self.app.startrequest()
    
    def tearDown(self):
        self.app.endrequest()
        self.app = None
    
    def test_routes(self):
        self.assertEqual('/prefix/url1', url_for('mod:Url1'))
        self.assertEqual('/prefix/url1?foo=bar', url_for('mod:Url1', foo='bar'))
        self.assertEqual('http://localhost/prefix/url1', url_for('mod:Url1', True))
        self.assertEqual('/prefix/static/c/test.css', style_url('test.css'))
        self.assertEqual('/prefix/foo/static/c/test.css', style_url('test.css', app='foo'))
        self.assertEqual('/prefix/static/js/test.js', js_url('test.js'))
        self.assertEqual('/prefix/foo/static/js/test.js', js_url('test.js', app='foo'))
        self.assertEqual('/prefix/', index_url())

class TestNoIndex(unittest.TestCase):
    def setUp(self):
        pysmvt.config.appinit(__import__(__name__), 'Noindex')
        self.app = Application()
        self.app.startrequest()
    
    def tearDown(self):
        self.app.endrequest()
        self.app = None
    
    def test_routes(self):
        self.assertEqual('/', index_url())

if __name__ == '__main__':
    unittest.main()
