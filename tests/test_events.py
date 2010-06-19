from nose.tools import eq_
from webtest import TestApp

from pysmvt import settings
from pysmvt.events import signal
from pysmvt.hierarchy import visitmods
from pysmvt.middleware import minimal_wsgi_stack
from pysmvt.application import WSGIApp

import config
from newlayout.config.settings import Default
from minimal2.config.settings import Default as DefaultM2

called = []

class EventTestApp(WSGIApp):
    def init_events(self):
        global called
        visitmods('events')
        called = signal('pysmvt.events.initialized').send(self.init_events)

class TestEvents(object):

    def test_event(self):
        nlapp = EventTestApp(Default())
        assert called[0][1] == 'newlayout', called

        nlta = TestApp(minimal_wsgi_stack(nlapp))
        r = nlta.get('/eventtest')
        r.mustcontain('foonewlayout')

        m2app = EventTestApp(DefaultM2())
        assert called[0][1] == 'minimal2', called

        m2ta = TestApp(minimal_wsgi_stack(m2app))
        r = m2ta.get('/eventtest')
        r.mustcontain('foominimal2')

        r = nlta.get('/eventtest')
        r.mustcontain('foonewlayout')


