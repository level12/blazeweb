import config
import unittest

import pysmvt
import pysmvttestapp.settings
from pysmvt.config import appslist

class TestConfig(unittest.TestCase):
    def setUp(self):
        pysmvt.config.appinit(pysmvttestapp.settings, 'Testruns')
        #self.app = Application()
        
    def tearDown(self):
        pass
        #self.app.endrequest()
        #self.app = None
        
    def test_appslist(self):
        self.assertEqual(['pysmvttestapp', 'pysmvttestapp2'], appslist())
        self.assertEqual(['pysmvttestapp2', 'pysmvttestapp'], appslist(reverse=True))

if __name__ == '__main__':
    unittest.main()
    #unittest.TextTestRunner().run(TestImports('test_callerglobals1'))
