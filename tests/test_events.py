from nose.tools import eq_
from webtest import TestApp

from blazeweb.globals import settings
from blazeweb.events import signal
from blazeweb.hierarchy import visitmods
from blazeweb.middleware import minimal_wsgi_stack
from blazeweb.application import WSGIApp

import config
from newlayout.config.settings import WithTestSettings
from minimal2.config.settings import EventSettings

called = []

class EventTestApp(WSGIApp):
    def init_events(self):
        global called
        visitmods('events')
        called = signal('blazeweb.events.initialized').send(self.init_events)

class TestEvents(object):

    def test_event(self):
        nlapp = EventTestApp(WithTestSettings())
        assert called[0][1] == 'newlayout', called

        nlta = TestApp(minimal_wsgi_stack(nlapp))
        r = nlta.get('/eventtest')
        r.mustcontain('foonewlayout')

        m2app = EventTestApp(EventSettings())
        assert called[0][1] == 'minimal2', called

        m2ta = TestApp(minimal_wsgi_stack(m2app))
        r = m2ta.get('/eventtest')
        r.mustcontain('foominimal2')

        r = nlta.get('/eventtest')
        r.mustcontain('foonewlayout')
