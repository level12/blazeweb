from webtest import TestApp
from pysmvt import ag

c = TestApp(ag.wsgiapp)

def test_something():
    r = c.get('/')
    assert 'index' in r

