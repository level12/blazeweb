import unittest
import os
import os.path as path
import rcsutils
import copy

# setup the virtual environment so that we can import specific versions
# of system libraries but also ensure that our pysmvt module is what
# we are pulling from
rcsutils.setup_virtual_env('pysmvt-libs-trunk', __file__, '..', '..', '..', '..')

from pysmvttestapp.application import Webapp
from werkzeug import Client, BaseResponse
from pysmvt.application import request_context_manager as rcm
from pysmvt.exceptions import ProgrammingError

class TestViews(unittest.TestCase):
        
    def setUp(self):
        self.app = Webapp('Testruns')
        self.client = Client(self.app, BaseResponse)
        
    def tearDown(self):
        self.client = None
        rcm.cleanup()
    
    def test_responding_view_base(self):
        r = self.client.get('tests/rvb')
        
        self.assertEqual(r.status, '200 OK')
        self.assertEqual(r.data, 'Hello World!')
            
    def test_responding_view_base_with_snippet(self):
        r = self.client.get('tests/rvbwsnip')
        
        self.assertEqual(r.status, '200 OK')
        self.assertEqual(r.data, 'Hello World!')
            
    def test_get(self):
        r = self.client.get('tests/get')
        
        self.assertEqual(r.status, '200 OK')
        self.assertEqual(r.data, 'Hello World!')            
    
    def test_post(self):
        r = self.client.post('tests/post')
        
        self.assertEqual(r.status, '200 OK')
        self.assertEqual(r.data, 'Hello World!')       
    
    def test_404_noroute(self):
        r = self.client.get('nothere')
        
        self.assertEqual(r.status, '404 NOT FOUND')
        self.assertTrue('Not Found' in r.data)
        self.assertTrue('If you entered the URL manually please check your spelling and try again.' in r.data)

    def test_nomodule(self):
        try:
            r = self.client.get('tests/badmod')
            self.fail('should have got ProgrammingError since URL exists but module does not')
        except ProgrammingError, e:
            self.assertEqual( 'Could not load view "fatfinger:NotExistant": cannot import module modules.fatfinger.views', str(e))
            
    def test_noview(self):
        try:
            r = self.client.get('tests/noview')
            self.fail('should have got ProgrammingError since URL exists but view does not')
        except ProgrammingError, e:
            self.assertEqual( 'Could not load view "tests:NotExistant": cannot import name NotExistant', str(e))
            
    def test_prep(self):
        r = self.client.get('tests/prep')
        
        self.assertEqual(r.status, '200 OK')
        self.assertEqual(r.data, 'Hello World!')
    
    def test_noactionmethod(self):
        try:
            r = self.client.get('tests/noactionmethod')
        except ProgrammingError, e:
            self.assertTrue( 'there were no "action" methods on the view class "tests:NoActionMethod"' in str(e))
        else:
            self.fail('should have gotten an exception b/c view does not have action method')
    
    def test_hideexception(self):
        self.app.settings.controller.hide_exceptions = True
        r = self.client.get('tests/noactionmethod')
        self.assertEqual(r.status, '500 INTERNAL SERVER ERROR')
        
    def test_2gets(self):
        r = self.client.get('tests/get')
        
        self.assertEqual(r.status, '200 OK')
        self.assertEqual(r.data, 'Hello World!')    
        
        r = self.client.get('tests/get')
        self.assertEqual(r.status, '200 OK')
        self.assertEqual(r.data, 'Hello World!')
        
    def test_tworespondingviews(self):
        try:
            r = self.client.get('tests/tworespondingviews')
        except ProgrammingError, e:
            self.assertTrue( 'Responding view (tests:Rvb) intialized but one already exists' in str(e))
        else:
            self.fail('should have gotten an exception b/c we initialized two responding views in the same request')
        
    def test_forward(self):
        r = self.client.get('tests/doforward')
        
        self.assertEqual(r.status, '200 OK')
        self.assertEqual(r.data, 'forward to me')
        
    def test_badforward(self):
        try:
            r = self.client.get('tests/badforward')
        except ProgrammingError, e:
            self.assertTrue( 'forward to non-RespondingViewBase view "HwSnippet"' in str(e))
        else:
            self.fail('should have gotten an exception b/c we forwarded to a non-responding view')
    
    def test_badroute(self):
        try:
            r = self.client.get('tests/badroute')
        except ProgrammingError, e:
            self.assertEqual( 'Route exists to non-RespondingViewBase view "HwSnippet"', str(e))
        else:
            self.fail('should have gotten an exception b/c we routed to a non-responding view')

    def test_text(self):
        r = self.client.get('tests/text')
        
        self.assertEqual(r.status, '200 OK')
        self.assertEqual(r.data, 'Hello World!')        
        self.assertEqual( dict(r.header_list)['Content-Type'], 'text/plain; charset=utf-8' )
        
    def test_textwsnip(self):
        r = self.client.get('tests/textwsnip')
        
        self.assertEqual(r.status, '200 OK')
        self.assertEqual(r.data, 'Hello World!')
        self.assertEqual( dict(r.header_list)['Content-Type'], 'text/plain; charset=utf-8' )

    def test_textwsnip2(self):
        r = self.client.get('tests/textwsnip2')
        
        self.assertEqual(r.status, '200 OK')
        self.assertEqual(r.data, 'Hello World!')
        self.assertEqual( dict(r.header_list)['Content-Type'], 'text/plain; charset=utf-8' )
    
    def test_html(self):
        r = self.client.get('tests/html')
        
        self.assertEqual(r.status, '200 OK')
        self.assertEqual(r.data, 'Hello World!')
        self.assertEqual( dict(r.header_list)['Content-Type'], 'text/html; charset=utf-8' )
    
    def test_htmljscss(self):
        r = self.client.get('tests/htmlcssjs')
        
        self.assertEqual(r.status, '200 OK')
        self.assertEqual(r.data, 'css\njs')
        self.assertEqual( dict(r.header_list)['Content-Type'], 'text/html; charset=utf-8' )

if __name__ == '__main__':
    unittest.main()

