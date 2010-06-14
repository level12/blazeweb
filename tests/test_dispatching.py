from helpers import create_testapp, create_altstack_app
from webtest import TestApp

from pysmvt import session, user, forward
from pysmvt.views import asview

wsgiapp = None
ta = None

class TestAltStack(object):

    @classmethod
    def setup_class(cls):
        cls.wsgiapp = create_altstack_app()
        cls.ta = TestApp(cls.wsgiapp)

    def test_workingview(self):
        @asview()
        def workingview():
            return 'hello foo!'

        r = self.ta.get('/workingview')
        r.mustcontain('hello foo!')

    def test_no_session(self):
        @asview()
        def nosession():
            assert not session
            # but we still have a user object, even though info won't get persisted
            assert user
            return 'hello nosession!'

        r = self.ta.get('/nosession')
        r.mustcontain('hello nosession!')

    def test_forward(self):
        @asview()
        def page1():
            forward('__viewfuncs__:page2')
            return 'hello nosession!'

        @asview()
        def page2():
            return 'page2!'

        r = self.ta.get('/page1')
        r.mustcontain('page2!')

class TestAltStackWithSession(object):

    @classmethod
    def setup_class(cls):
        cls.wsgiapp = create_altstack_app(use_session=True)
        cls.ta = TestApp(cls.wsgiapp)

    def test_workingview(self):
        @asview()
        def workingview():
            return 'hello foo!'

        r = self.ta.get('/workingview')
        r.mustcontain('hello foo!')

    def test_hassession(self):
        @asview()
        def hassession():
            assert session
            assert user
            return 'hello hassession!'

        r = self.ta.get('/hassession')
        r.mustcontain('hello hassession!')

    def test_session_saves(self):
        @asview()
        def session1():
            session['session1'] = 'foo'
            return ''

        r = self.ta.get('/session1')

        @asview()
        def session2():
            assert session['session1'] == 'foo'
            return ''

        r = self.ta.get('/session2')

        @asview()
        def session3():
            assert 'session1' not in session
            return ''

        nta = TestApp(self.wsgiapp)
        r = nta.get('/session3')
