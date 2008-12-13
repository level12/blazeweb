import config
import unittest

from pysmvt.application import Application
import pysmvt.config
from pysmvt.routing import *
from pysmvt.exceptions import SettingsError

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

class Noindex(RoutingSettings):
    def __init__(self):
        RoutingSettings.__init__(self)
        
        self.routing.routes = [
            Rule('/url1', endpoint='mod:Url1'),
        ]

class TestRouting(unittest.TestCase):
    def setUp(self):
        pysmvt.config.appinit(__import__(__name__).test_routing, 'RoutingSettings')
        self.app = Application()
        self.app.startrequest()
    
    def tearDown(self):
        self.app.endrequest()
        self.app = None
    
    def test_routes(self):
        self.assertEqual( '/url1', url_for('mod:Url1'))
        self.assertEqual('/url1?foo=bar', url_for('mod:Url1', foo='bar'))
        self.assertEqual('http://localhost/url1', url_for('mod:Url1', True))
        self.assertEqual('/c/test.css', style_url('test.css'))
        self.assertEqual('/c/test.css', style_url('test.css', app='foo'))
        self.assertEqual('/js/test.js', js_url('test.js'))
        self.assertEqual('/js/test.js', js_url('test.js', app='foo'))
        self.assertEqual('/', index_url())

class TestPrefix(unittest.TestCase):
    def setUp(self):
        pysmvt.config.appinit(__import__(__name__).test_routing, 'Prefixsettings')
        self.app = Application()
        self.app.startrequest()
    
    def tearDown(self):
        self.app.endrequest()
        self.app = None
    
    def test_routes(self):
        self.assertEqual('/prefix/url1', url_for('mod:Url1'))
        self.assertEqual('/prefix/url1?foo=bar', url_for('mod:Url1', foo='bar'))
        self.assertEqual('http://localhost/prefix/url1', url_for('mod:Url1', True))
        self.assertEqual('/prefix/c/test.css', style_url('test.css'))
        self.assertEqual('/prefix/c/test.css', style_url('test.css', app='foo'))
        self.assertEqual('/prefix/js/test.js', js_url('test.js'))
        self.assertEqual('/prefix/js/test.js', js_url('test.js', app='foo'))
        self.assertEqual('/prefix/', index_url())

class TestNoIndex(unittest.TestCase):
    def setUp(self):
        pysmvt.config.appinit(__import__(__name__).test_routing, 'Noindex')
        self.app = Application()
        self.app.startrequest()
    
    def tearDown(self):
        self.app.endrequest()
        self.app = None
    
    def test_routes(self):
        
        try:
            index_url()
            self.fail('expected exception from index_url()')
        except SettingsError, e:
            self.assertEqual('the index url "/" could not be located', str(e))

if __name__ == '__main__':
    unittest.main()
