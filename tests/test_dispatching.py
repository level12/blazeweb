from helpers import create_testapp, asview
from webtest import TestApp

wsgiapp = None
ta = None

def setup_module():
    global wsgiapp, ta
    wsgiapp = create_testapp()
    ta = TestApp(wsgiapp)

def test_working_view():

    @asview
    def workingview():
        return 'hello world!'
        
    r = ta.get('/workingview')
    r.mustcontain('hello world!')
    
