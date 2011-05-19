from blazeweb.globals import ag, settings
from blazeweb.testing import TestApp

class TestViews(object):

    @classmethod
    def setup_class(cls):
        cls.ta = TestApp(ag.wsgi_test_app)

    def test_index(self):
        r = self.ta.get('/')
        assert 'Hello World' in r, r
