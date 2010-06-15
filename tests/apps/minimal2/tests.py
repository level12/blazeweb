from webtest import TestApp
from pysmvt import ag

c = TestApp(ag.wsgi_test_app)

def test_something():
    r = c.get('/')
    assert 'index' in r
