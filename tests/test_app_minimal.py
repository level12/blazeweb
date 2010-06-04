from webtest import TestApp

from pysmvt import settings

# make sure the path gets appended so we can import by name
import config
from minimal1.application import wsgiapp, settings
settings.apply_test_settings()

class TestViews(object):
    
    @classmethod
    def setup_class(cls):
        cls.ta = TestApp(wsgiapp)
    
    def test_workingview(self):           
        r = self.ta.get('/helloworld')
        r.mustcontain('Hello World')
    
    def test_mms(self):           
        r = self.ta.get('/mms')
        r.mustcontain('make_me_shorter')
        
    def test_tome(self):           
        r = self.ta.get('/hw/itisme')
        r.mustcontain('Hello itisme')
        r = self.ta.get('/hw2/itisme')
        r.mustcontain('hw2 itisme')
        
    def test_flexible(self):           
        r = self.ta.get('/flexible/foo')
        r.mustcontain('thats cool')
        
    def test_getargs(self):           
        r = self.ta.get('/cooler/hot?foo=1&bar=2&willstaynone=3')
        r.mustcontain('1, 2, hot, None')
    
    def test_argprec(self):
        r = self.ta.get('/ap/2?foo=1')
        r.mustcontain("[u'1', u'2']")
    
    def test_list(self):
        r = self.ta.get('/tolist?foo=1&foo=2')
        r.mustcontain("[u'1', u'2']")
    
    def test_badargspec(self):
        r = self.ta.get('/wontwork?foo=1', status=400)
        assert r.status_int == 400
        
        r = self.ta.get('/positional3/posurlok', status=400)
        assert r.status_int == 400
    
    def test_positional(self):
        r = self.ta.get('/positional?foo=posok')
        r.mustcontain("posok")
        
    def test_positionalurl(self):
        r = self.ta.get('/positional/posurlok')
        r.mustcontain("posurlok")
        
    def test_request_modified_directly(self):
        r = self.ta.get('/cssresponse')
        r.mustcontain('body {color:black}')
        assert 'text/css' in r.headers['content-type']
        
    def test_return_wsgiapp(self):
        r = self.ta.get('/returnwsgiapp')
        r.mustcontain('wsgi hw')
        