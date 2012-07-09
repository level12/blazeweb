import unittest

from werkzeug import Client, BaseResponse

from blazeutils.jsonh import jsonmod
from blazeweb.globals import settings, user
from blazeweb.exceptions import ProgrammingError
from blazeweb.hierarchy import HierarchyImportError

import config
from blazewebtestapp.applications import make_wsgi
from blazewebtestapp2.applications import make_wsgi as make_wsgi2


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
        except HierarchyImportError, e:
            assert 'An object for View endpoint "fatfinger:NotExistant" was not found' == str(e), e

    def test_noview(self):
        try:
            r = self.client.get('tests/noview')
            self.fail('should have got ProgrammingError since URL exists but view does not')
        except HierarchyImportError, e:
            assert 'An object for View endpoint "tests:NotExistant" was not found' == str(e), e

    def test_prep(self):
        r = self.client.get('tests/prep')

        self.assertEqual(r.status, '200 OK')
        self.assertEqual(r.data, 'Hello World!')

    def test_hideexception(self):
        settings.exception_handling = ['handle']
        r = self.client.get('tests/raiseexc')
        self.assertEqual(r.status, '500 INTERNAL SERVER ERROR')

    def test_2gets(self):
        r = self.client.get('tests/get')

        self.assertEqual(r.status, '200 OK')
        self.assertEqual(r.data, 'Hello World!')

        r = self.client.get('tests/get')
        self.assertEqual(r.status, '200 OK')
        self.assertEqual(r.data, 'Hello World!')

    def test_forward(self):
        r = self.client.get('tests/doforward')

        self.assertEqual(r.status, '200 OK')
        self.assertEqual(r.data, 'forward to me')

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
        settings.error_docs[503] = 'tests:RaiseExc'
        try:
            r = self.client.get('tests/heraise')
        except ValueError, e:
            self.assertTrue( 'exception for testing' in str(e))
        else:
            self.fail('should have gotten an exception b/c our error handler raised one')

        # now turn exception handling on and we should see a generic 500
        # response since the document handler raised an exception
        settings.exception_handling = ['handle']
        r = self.client.get('tests/heraise')

        self.assertEqual(r.status_code, 500)
        assert 'Internal Server Error' in r.data

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
        # we are no longer going to manipulate the response object to include
        # user messages
        self.assertTrue('integer' not in r.data)

        #If you want user messages included in an error response
        # you need to use an error document that will include them, like so:
        settings.error_docs[400] = 'tests:UserMessages'
        r = self.client.get('tests/getargs3?num=ten&num2=ten')
        self.assertEqual(r.status_code, 400)
        assert '(error) num2: num: must be an integer' in r.data, r.data
        assert '(error) num: Please enter an integer value' in r.data, r.data

    def test_reqgetargs(self):
        settings.error_docs[400] = 'tests:UserMessages'
        r = self.client.get('/tests/reqgetargs?num=10&num2=10')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data, 'Hello World, 10 10 10!')

        r = self.client.get('/tests/reqgetargs?num2=ten')
        self.assertEqual(r.status_code, 400)
        self.assertTrue('(error) num: Please enter a value' in r.data, r.data)
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
        self.assertEqual(r.data, '[2]')

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
            self.assertEqual( 'processor must be a Formencode validator or a callable', str(e))
        else:
            self.fail('excpected exception for bad validator')

    def test_static(self):
        r = self.client.get('/static/app/helloworld.html')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data, 'Hello World!')

        r = self.client.get('/static/app/helloworld2.html')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data.strip(), 'Hellow blazewebtestapp2!')

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

    def test_disabled_module(self):
        """ a disabled module should not be processed and therefore we should
        get a 404"""
        r = self.client.get('/disabled/notthere')

        self.assertEqual(r.status, '404 NOT FOUND')
        self.assertTrue('Not Found' in r.data)
        self.assertTrue('If you entered the URL manually please check your spelling and try again.' in r.data)

    def test_render_endpoint(self):
        # app level endpoint
        r = self.client.get('/tests/tchooser/endpoint')
        assert 'app level' in r.data, r.data

        # render content
        r = self.client.get('/tests/tchooser/content')
        assert 'Hello World!' in r.data, r.data

    def test_render_template_directly(self):
        # app level endpoint
        r = self.client.get('/tests/text.txt/&fred')
        assert r.headers['Content-Type'] == 'text/plain; charset=utf-8', r.headers
        assert 'Hello &amp;fred!' in r.data, r.data

    def test_jsonify_exception(self):
        # we have exception handling turned off during testing, so we should
        # get the exception passed all the way up
        try:
            r = self.client.get('/jsonify-exception')
            assert False
        except NameError, e:
            if 'foo' not in str(e):
                raise

        try:
            settings.exception_handling = ['handle']
            r = self.client.get('/jsonify-exception')
            assert r.status_code == 500, r.status_code
            data = jsonmod.loads(r.data)
            assert data['error'] == 1, data
            assert data['data'] is None, data
        finally:
            settings.exception_handling = None

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
