import unittest

from pysmvttestapp.applications import make_wsgi
from werkzeug import Client, BaseResponse

#########################################################################
#NOTE: TESTS WILL FAIL UNTIL BUG IN WERKZUEG IS PATCHED
#http://dev.pocoo.org/projects/werkzeug/ticket/383
#########################################################################

class TestSession(unittest.TestCase):
        
    def setUp(self):
        self.app = make_wsgi('Testruns')
        #settings.logging.levels.append(('debug', 'info'))
        self.client = Client(self.app, BaseResponse)
        
    def tearDown(self):
        self.client = None
        self.app = None
    
    def test_session_persist(self):
        r = self.client.get('/sessiontests/setfoo')
        
        self.assertEqual(r.status, '200 OK')
        self.assertEqual(r.data, 'foo set')
        
        r = self.client.get('/sessiontests/getfoo')

        self.assertEqual(r.status, '200 OK')
        self.assertEqual(r.data, 'bar')
            
