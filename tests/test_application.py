from nose.tools import eq_

from blazeutils.datastructures import BlankObject
from webtest import TestApp
from werkzeug import run_wsgi_app

from blazeweb import settings, ag, rg

import config
from newlayout.application import make_wsgi

def test_plugin_settings():
    app = make_wsgi()

    assert settings.plugins.news.foo == 1
    assert settings.plugins.news.bar == 3
    assert settings.plugins.pnoroutes.noroutes == True

    assert "<Rule '/fake/route' -> news:notthere>" in str(ag.route_map), ag.route_map

def test_bad_settings_profile():
    try:
        app = make_wsgi('notthere')
        assert False
    except ValueError, e:
        assert 'settings profile "notthere" not found in this application' == str(e), e

    try:
        app = make_wsgi('AttributeErrorInSettings')
        assert False
    except AttributeError, e:
        assert "'module' object has no attribute 'notthere'" == str(e), e

def test_environ_hooks():
    tracker = []
    class TestMiddleware(object):
        def __init__(self, app):
            self.app = app

        def __call__(self, environ, start_response):
            def request_setup():
                rg.testattr = 'foo'
                tracker.append('reqs')
            def request_teardown():
                tracker.append('reqt')
            def response_setup():
                tracker.append('resps')
            def response_teardown():
                tracker.append('respt')
            environ.setdefault('blazeweb.request_setup', [])
            environ.setdefault('blazeweb.request_teardown', [])
            environ.setdefault('blazeweb.response_cycle_setup', [])
            environ.setdefault('blazeweb.response_cycle_teardown', [])
            environ['blazeweb.request_setup'].append(request_setup)
            environ['blazeweb.request_teardown'].append(request_teardown)
            environ['blazeweb.response_cycle_setup'].append(response_setup)
            environ['blazeweb.response_cycle_teardown'].append(response_teardown)
            return self.app(environ, start_response)
    app = TestMiddleware(make_wsgi())
    ta = TestApp(app)

    r = ta.get('/news')
    r.mustcontain('news index')
    eq_(tracker, ['reqs', 'resps','respt','reqt'])
    tracker = []

    r = ta.get('/news/reqsetupattr')
    r.mustcontain('foo')

