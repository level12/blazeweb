from nose.tools import eq_

from blazeutils.datastructures import BlankObject
from webtest import TestApp
from werkzeug import run_wsgi_app

from blazeweb.globals import settings, ag, rg

import config
from newlayout.application import make_wsgi
from minimal2.application import make_wsgi as m2_make_wsgi

def test_component_settings():
    app = make_wsgi()

    assert settings.components.news.foo == 1
    eq_(settings.components.news.bar, 3)
    assert settings.components.pnoroutes.noroutes == True

    assert "<Rule '/fake/route' -> news:notthere>" in str(ag.route_map), ag.route_map

def test_external_component_settings():
    app = m2_make_wsgi('Dispatching')

    # an internal-only component
    assert settings.components.news.min2news == 'internal'
    # an external-only component
    assert settings.components.foo.fooattr == True

    # an application level setting from a component
    assert settings.setting_from_component == 'minimal2'

    # components can add/change the app's current settings
    eq_(settings.some_list, ['from app', 'minimal2'])

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

class TestUserSessionInteraction(object):

    @classmethod
    def setup_class(cls):
        cls.app = make_wsgi('WithTestSettings')

    def test_user_added_to_session_only_when_accessed(self):
        ta = TestApp(self.app)
        r = ta.get('/applevelview/foo')
        assert r.user is None
        assert r.session.accessed() == False

    def test_user_added_when_accessed(self):
        ta = TestApp(self.app)
        r = ta.get('/index/index')
        assert '<User (' in repr(r.user)
        assert r.session.has_key('__blazeweb_user')
        assert r.session.accessed() == True

    def test_framework_hook(self):
        ta = TestApp(self.app)
        r = ta.get('/index/index')

        # user attribute set
        assert r.user.foo == 'bar'

        # session item set
        assert r.session['foo'] == 'bar2'
