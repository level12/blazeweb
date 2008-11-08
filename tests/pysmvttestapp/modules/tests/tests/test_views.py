import unittest
import os
import os.path as path
import rcsutils

# setup the virtual environment so that we can import specific versions
# of system libraries but also ensure that our pysmvt module is what
# we are pulling from
rcsutils.setup_virtual_env('pysmvt-libs-trunk', __file__, '..', '..', '..', '..')

from pysmvttestapp.application import Webapp
from werkzeug import Client, BaseResponse
from pysmvt.application import request_context_manager as rcm

class TestViews(unittest.TestCase):
    def setUp(self):
        self.app = Webapp('Testruns')
        self.client = Client(self.app, BaseResponse)
    
    def test_responding_view_base(self):
        r = self.client.get('tests/rvb')
        
        self.assertEqual(r.status, '200 OK')
        self.assertEqual(r.data, 'Hello World!')
            
    def test_responding_view_base_with_snippet(self):
        r = self.client.get('tests/rvbwsnip')
        
        self.assertEqual(r.status, '200 OK')
        self.assertEqual(r.data, 'Hello World!')
        
    def tearDown(self):
        self.client = None
        self.app = None
        rcm.cleanup()

if __name__ == '__main__':
    unittest.main()
