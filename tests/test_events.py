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
        # newlayout event should fire, it should be the only one
        nlapp = EventTestApp(WithTestSettings())
        assert len(called) == 1, called
        assert called[0][1] == 'newlayout', called

        # do a functional tests, which uses the event
        # blazeweb.response_cycle.ended to append the string 'newlayout' to the
        # response of the requested view (in this case, "foo")
        nlta = TestApp(minimal_wsgi_stack(nlapp))
        r = nlta.get('/eventtest')
        r.mustcontain('foonewlayout')

        # instantiate the minimal2 application, only one event, the one from that
        # app, should fire
        m2app = EventTestApp(EventSettings())
        assert len(called) == 1, called
        assert called[0][1] == 'minimal2', called

        # same as above, but the minimal2 application is modifying the request
        m2ta = TestApp(minimal_wsgi_stack(m2app))
        r = m2ta.get('/eventtest')
        r.mustcontain('foominimal2')

        # now that we have instantiated the minimal2 application, we want to
        # make sure that request level events for the newlayout application are
        # still working as expected
        r = nlta.get('/eventtest')
        r.mustcontain('foonewlayout')

    def test_connect_to_signal_decorator(self):
        # this initialized the application and sets up the settings
        import minimal3.application
        assert settings.logging_is_initialized

        # make sure the class doesn't have the attribute
        assert not hasattr(settings.__class__, 'logging_is_initialized')
