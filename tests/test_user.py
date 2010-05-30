import unittest

from pysmvttestapp.applications import make_wsgi
from werkzeug import Client, BaseResponse

#########################################################################
#NOTE: TESTS WILL FAIL UNTIL BUG IN WERKZUEG IS PATCHED
#http://dev.pocoo.org/projects/werkzeug/ticket/383
#########################################################################

class TestUser(unittest.TestCase):
        
    def setUp(self):
        self.app = make_wsgi('Testruns')
        #settings.logging.levels.append(('debug', 'info'))
        self.client = Client(self.app, BaseResponse)
        
    def tearDown(self):
        self.client = None
        self.app = None
    
    def test_attr(self):
        r = self.client.get('/usertests/setfoo')
        
        self.assertEqual(r.status, '200 OK')
        self.assertEqual(r.data, 'foo set')
        
        r = self.client.get('/usertests/getfoo')

        self.assertEqual(r.status, '200 OK')
        self.assertEqual(r.data, 'barbaz')

    def test_auth(self):
        r = self.client.get('/usertests/setauth')

        self.assertEqual(r.status, '200 OK')

        r = self.client.get('/usertests/getauth')

        self.assertEqual(r.status, '200 OK')
        self.assertEqual(r.data, 'True')

    def test_perm(self):
        r = self.client.get('/usertests/addperm')

        self.assertEqual(r.status, '200 OK')

        r = self.client.get('/usertests/getperms')

        self.assertEqual(r.status, '200 OK')
        self.assertEqual(r.data, 'TrueFalse')

    def test_clear(self):
        r = self.client.get('/usertests/clear')

        self.assertEqual(r.status, '200 OK')
        self.assertEqual(r.data, 'FalseFalseNone')

    def test_message(self):
        r = self.client.get('/usertests/setmsg')

        self.assertEqual(r.status, '200 OK')

        r = self.client.get('/usertests/getmsg')

        self.assertEqual(r.status, '200 OK')
        self.assertEqual(r.data, 'test: my message')

        r = self.client.get('/usertests/nomsg')

        self.assertEqual(r.status, '200 OK')
        self.assertEqual(r.data, '0')