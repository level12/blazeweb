import unittest

from pysmvt import settings
from pysmvttestapp.applications import make_wsgi
from pysmvttestapp2.applications import make_wsgi as make_wsgi2
from werkzeug import Client, BaseResponse
from pysmvt.exceptions import ProgrammingError

class TestViews(unittest.TestCase):
        
    def setUp(self):
        self.app = make_wsgi('Testruns')
        #settings.logging.levels.append(('debug', 'info'))
        self.client = Client(self.app, BaseResponse)
        
    def tearDown(self):
        self.client = None
        self.app = None
    
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
            self.assertEqual( 'Could not load view "fatfinger:NotExistant": cannot import "modules.fatfinger.views" with attribute "NotExistant" from any application', str(e))
            
    def test_noview(self):
        try:
            r = self.client.get('tests/noview')
            self.fail('should have got ProgrammingError since URL exists but view does not')
        except ProgrammingError, e:
            self.assertEqual( 'Could not load view "tests:NotExistant": cannot import "modules.tests.views" with attribute "NotExistant" from any application', str(e))
            
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
        settings.exceptions.hide = True
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
        self.assertEqual( r.headers['Content-Type'], 'text/plain; charset=utf-8' )
        
    def test_textwsnip(self):
        r = self.client.get('tests/textwsnip')
        
        self.assertEqual(r.status, '200 OK')
        self.assertEqual(r.data, 'Hello World!')
        self.assertEqual( r.headers['Content-Type'], 'text/plain; charset=utf-8' )

    def test_textwsnip2(self):
        r = self.client.get('tests/textwsnip2')
        
        self.assertEqual(r.status, '200 OK')
        self.assertEqual(r.data, 'Hello World!')
        self.assertEqual( r.headers['Content-Type'], 'text/plain; charset=utf-8' )
    
    def test_html(self):
        r = self.client.get('tests/html')
        
        self.assertEqual(r.status, '200 OK')
        self.assertEqual(r.data, 'Hello World!')
        self.assertEqual( r.headers['Content-Type'], 'text/html; charset=utf-8' )
    
    def test_htmljscss(self):
        r = self.client.get('tests/htmlcssjs')
        
        self.assertEqual(r.status, '200 OK')
        self.assertEqual(r.data, 'css\njs')
        self.assertEqual( r.headers['Content-Type'], 'text/html; charset=utf-8' )
    
    def test_redirect(self):
        r = self.client.get('tests/redirect')
        
        self.assertEqual(r.status_code, 302)
        self.assertEqual(r.headers['Location'], 'http://localhost/some/other/page')
        
    def test_permredirect(self):
        r = self.client.get('tests/permredirect')
        
        self.assertEqual(r.status_code, 301)
        self.assertEqual(r.headers['Location'], 'http://localhost/some/other/page')
        
    def test_custredirect(self):
        r = self.client.get('tests/custredirect')
        
        self.assertEqual(r.status_code, 303)
        self.assertEqual(r.headers['Location'], 'http://localhost/some/other/page')
        
    def test_heraise(self):
        r = self.client.get('tests/heraise')
        
        self.assertEqual(r.status_code, 503)
        assert 'server is temporarily unable' in r.data
    
    def test_errordoc(self):
        settings.error_docs[503] = 'tests:Rvb'
        r = self.client.get('tests/heraise')
        
        self.assertEqual(r.status_code, 503)
        self.assertEqual(r.status, '503 SERVICE UNAVAILABLE')
        self.assertEqual(r.data, 'Hello World!')

    def test_errordocexc(self):
        settings.error_docs[503] = 'tests:BadForward'
        try:
            r = self.client.get('tests/heraise')
        except ProgrammingError, e:
            self.assertTrue( 'forward to non-RespondingViewBase view "HwSnippet"' in str(e))
        else:
            self.fail('should have gotten an exception b/c we forwarded to a non-responding view')
        
        # now turn exception handling on, and we should see the original
        # non-200 response since the exception created by tests:BadForward
        # should have been turned into a 500 response, which the error docs
        # handler won't accept
        settings.exceptions.hide = True
        r = self.client.get('tests/heraise')
        
        self.assertEqual(r.status_code, 503)
        self.assertEqual(r.status, '503 SERVICE UNAVAILABLE')
        assert 'server is temporarily unable' in r.data
    
    def test_forwardloop(self):
        try:
            r = self.client.get('tests/forwardloop')
        except ProgrammingError, e:
            self.assertTrue( 'forward loop detected:' in str(e))
        else:
            self.fail('excpected exception for a forward loop')

    def test_urlargs(self):
        r = self.client.get('tests/urlargs')
        
        self.assertEqual(r.status, '200 OK')
        self.assertEqual(r.data, 'Hello World!')
        
        r = self.client.get('tests/urlargs/fred')
        
        self.assertEqual(r.status, '200 OK')
        self.assertEqual(r.data, 'Hello fred!')
        
        r = self.client.get('tests/urlargs/10')
        
        self.assertEqual(r.status, '200 OK')
        self.assertEqual(r.data, 'Give me a name!')
    
    def test_getargs(self):
        
        r = self.client.get('tests/getargs')
        self.assertEqual(r.status, '200 OK')
        self.assertEqual(r.data, 'Hello World!')
        
        r = self.client.get('tests/getargs?towho=fred&greeting=Hi&extra=bar')
        self.assertEqual(r.status, '200 OK')
        self.assertEqual(r.data, 'Hello fred!')

    
    def test_getargs2(self):
        
        r = self.client.get('tests/getargs2')
        self.assertEqual(r.status, '200 OK')
        self.assertEqual(r.data, 'Hello World!')
        
        r = self.client.get('tests/getargs2?towho=fred')
        self.assertEqual(r.status, '200 OK')
        self.assertEqual(r.data, 'Hello fred!')
        
        r = self.client.get('tests/getargs2?num=10')
        self.assertEqual(r.status, '200 OK')
        self.assertEqual(r.data, 'Hello World, 10!')
        
        r = self.client.get('tests/getargs2?num=ten')
        self.assertEqual(r.status, '200 OK')
        self.assertEqual(r.data, 'Hello World!')

    
    def test_getargs3(self):        
        r = self.client.get('tests/getargs3?num=ten&num2=ten')
        self.assertEqual(r.status_code, 400)
        self.assertTrue('(error) num: must be an integer' in r.data)
        self.assertTrue('(error) num: Please enter an integer value' in r.data)

    def test_reqgetargs(self):
        
        r = self.client.get('/tests/reqgetargs?num=10&num2=10')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data, 'Hello World, 10 10 10!')
        
        r = self.client.get('/tests/reqgetargs?num2=ten')
        self.assertEqual(r.status_code, 400)
        self.assertTrue('(error) num: argument required' in r.data)
        self.assertTrue('(error) num2: Please enter an integer value' in r.data)
        
        r = self.client.get('tests/reqgetargs?num1&num=2')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data, 'Hello World, 2 10 10!')
    
    def test_listgetargs(self):

        r = self.client.get('tests/listgetargs?nums=1&nums=2')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data, '[1, 2]')

        r = self.client.get('tests/listgetargs?nums=ten&nums=2')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data, '[]')
    
    def test_customvalidator(self):

        r = self.client.get('tests/customvalidator?num=asek')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data, '10')

        r = self.client.get('tests/customvalidator')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data, '10')

        r = self.client.get('tests/customvalidator?num=5')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data, '5')
        
    def test_badvalidator(self):
        try:
            r = self.client.get('tests/badvalidator')
        except TypeError, e:
            self.assertEqual( 'validator must be a Formencode validator or a callable', str(e))
        else:
            self.fail('excpected exception for bad validator')
        
    def test_static(self):
        r = self.client.get('helloworld.html')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data, 'Hello World!')
        
        r = self.client.get('helloworld2.html')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data, 'Hellow pysmvttestapp2!')

    def test_app2(self):
        # app2's test module won't have its settings imported
        # b/c app1's settings module is blocking it.  Therefore, the
        # route doesn't get added and we get a 404
        r = self.client.get('tests/rvbapp2')
        self.assertEqual(r.status_code, 404)
        
    def test_appfallback(self):
        r = self.client.get('tests/appfallback')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data, 'Hello app2!')
    
    def test_htmltemplateerror1(self):
        try:
            r = self.client.get('tests/htmltemplateerror1')
        except ProgrammingError, e:
            self.assertEqual( 'a view can only set template_name or template_file, not both', str(e))
        else:
            self.fail('excpected exception for bad template arguments')
    
    def test_htmltemplatefilearg(self):
        r = self.client.get('tests/htmltemplatefilearg')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data, 'Hello File Arg!')
    
    def test_htmltemplateinheritance(self):
        """ test inheritance at the module level from a supporting app """
        r = self.client.get('tests/templateinheritance')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data, 'Hello Template Inheritance!')

    def test_parenttemplate(self):
        """ test extending a template from the parent application """
        r = self.client.get('tests/parenttemplate')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data, 'Hello Parent Template!')

    def test_parenttemplateinheritance(self):
        """ test extending a template from a supporting app"""
        r = self.client.get('tests/parenttemplateinheritance')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data, 'Hello App2 Parent Template!')
        
    def test_modlevelpriority(self):
        """ make sure that when inheriting that a module level template in a
            supporting app takes precidence over a template level app in the
            main module
        """
        r = self.client.get('tests/modlevelpriority')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data, 'Hello mod level priority!')
        
    def test_htmltemplatefileargcss(self):
        r = self.client.get('tests/htmltemplatefileargcss')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data, 'css\nHello File Arg!')
          
    def test_disabled_module(self):
        """ a disabled module should not be processed and therefore we should
        get a 404"""
        r = self.client.get('/disabled/notthere')
        
        self.assertEqual(r.status, '404 NOT FOUND')
        self.assertTrue('Not Found' in r.data)
        self.assertTrue('If you entered the URL manually please check your spelling and try again.' in r.data)


class TestApp2(unittest.TestCase):
        
    def setUp(self):
        self.app = make_wsgi2('Testruns')
        #settings.logging.levels.append(('debug', 'info'))
        self.client = Client(self.app, BaseResponse)
        
    def tearDown(self):
        self.client = None
        self.app = None
        
    def test_app2(self):
        r = self.client.get('tests/rvbapp2')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data, 'Hello app2!')
    
    def test_underscore_templates(self):
        r = self.client.get('tests/underscoretemplates')
        
        self.assertEqual(r.status, '200 OK')
        self.assertEqual(r.data, 'Hello World!')
        self.assertEqual( r.headers['Content-Type'], 'text/html; charset=utf-8' )

if __name__ == '__main__':
    #unittest.main()
    tests = ['test_responding_view_base', 'test_responding_view_base_with_snippet']
    unittest.TextTestRunner().run(unittest.TestSuite(map(TestViews, tests)))

