import config
import unittest

from nose.tools import eq_
from werkzeug import Client, BaseResponse, create_environ

from blazeweb.globals import settings
from blazeweb.routing import *
from blazeweb.exceptions import SettingsError
from blazeweb.testing import inrequest

from blazewebtestapp.applications import make_wsgi

class RoutingSettings(config.Testruns):
    def init(self):
        config.Testruns.init(self)

        self.routing.routes.extend([
            Rule('/', endpoint='mod:Index'),
            Rule('/url1', endpoint='mod:Url1'),
        ])

class Prefixsettings(RoutingSettings):
    def init(self):
        RoutingSettings.init(self)

        self.routing.static_prefix = 'http://static.example.com/'

class TestRouting(unittest.TestCase):

    @classmethod
    def setup_class(cls):
        cls.app = config.make_wsgi(RoutingSettings)

    @inrequest()
    def test_routes(self):
        self.assertEqual( '/url1', url_for('mod:Url1'))
        self.assertEqual('/url1?foo=bar', url_for('mod:Url1', foo='bar'))
        self.assertEqual('http://localhost/url1', url_for('mod:Url1', True))
        self.assertEqual('https://localhost/url1', url_for('mod:Url1', _https=True))
        self.assertEqual('http://localhost/url1', url_for('mod:Url1', _https=False))

class TestRoutingSSL(unittest.TestCase):

    @classmethod
    def setup_class(cls):
        cls.app = config.make_wsgi(RoutingSettings)

    @inrequest("/test/url", "https://localhost:8080/script")
    def test_routes(self):
        self.assertEqual( '/script/url1', url_for('mod:Url1'))
        self.assertEqual('/script/url1?foo=bar', url_for('mod:Url1', foo='bar'))
        self.assertEqual('https://localhost:8080/script/url1', url_for('mod:Url1', True))
        self.assertEqual('https://localhost:8080/script/url1', url_for('mod:Url1', _https=True))
        self.assertEqual('http://localhost:8080/script/url1', url_for('mod:Url1', _https=False))

class TestRoutingSSLCaseSensitive(unittest.TestCase):

    @classmethod
    def setup_class(cls):
        cls.app = config.make_wsgi(RoutingSettings)

    @inrequest("/test/url", "HTTPS://localhost:8080/scRipt")
    def test_routes(self):
        self.assertEqual('https://localhost:8080/scRipt/url1', url_for('mod:Url1', True))
        self.assertEqual('https://localhost:8080/scRipt/url1', url_for('mod:Url1', _https=True))
        self.assertEqual('http://localhost:8080/scRipt/url1', url_for('mod:Url1', _https=False))

class TestPrefix(unittest.TestCase):

    @classmethod
    def setup_class(cls):
        cls.app = config.make_wsgi(Prefixsettings)

    @inrequest()
    def test_routes(self):
        eq_('http://static.example.com/app/c/styles.css', static_url('app/c/styles.css'))
        eq_('http://static.example.com/app/c/styles.css', static_url('/app/c/styles.css'))
        settings.routing.static_prefix = '/static'
        eq_('/static/app/c/styles.css', static_url('/app/c/styles.css'))

class TestCurrentUrl(unittest.TestCase):

    @classmethod
    def setup_class(cls):
        cls.app = make_wsgi('Testruns')
        cls.client = Client(cls.app, BaseResponse)

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

class TestProperUrl(object):
    @classmethod
    def setup_class(cls):
        # make sure an app is created, otherwise the tests can fail if this
        # test is run by itself
        cls.app = config.make_wsgi(RoutingSettings)

    def test_absolute(self):
        eq_(prefix_relative_url('https://example.com/the-page'), 'https://example.com/the-page')
        eq_(prefix_relative_url('http://example.com/the-page'), 'http://example.com/the-page')
        eq_(prefix_relative_url('/the-page'), '/the-page')
        eq_(prefix_relative_url('/'), '/')

    def test_relative_no_request(self):
        eq_(prefix_relative_url('the-page'), '/the-page')
        eq_(prefix_relative_url(''), '/')

    @inrequest("/foobar")
    def test_relative_in_request(self):
        eq_(prefix_relative_url('the-page'), '/the-page')
        eq_(prefix_relative_url(''), '/')

    @inrequest("/foobar", "https://localhost:8080/script")
    def test_relative_in_request_with_scriptname(self):
        eq_(prefix_relative_url('the-page'), '/script/the-page')
        eq_(prefix_relative_url(''), '/script/')
