from os import path
import unittest
import pysmvttestapp
import pysmvttestapp2
import pysmvttestapp.applications
import pysmvt
from pysmvt import appfilepath
from pysmvt.exceptions import ProgrammingError

app1_dir = path.dirname(pysmvttestapp.__file__)
app2_dir = path.dirname(pysmvttestapp2.__file__)

class TestImports(unittest.TestCase):
    def setUp(self):
        self.app = pysmvttestapp.applications.make_console('Testruns')
        self.app.start_request()
        
    def tearDown(self):
        self.app.end_request()
        self.app = None
        
    def test_locate1(self):
        appfilepath('settings.py') == path.join(app1_dir, 'settings.py')
        
    def test_locate2(self):
        appfilepath('not_in_app1.txt') == path.join(app2_dir, 'not_in_app1.txt')
        # test cache
        appfilepath('not_in_app1.txt') == path.join(app2_dir, 'not_in_app1.txt')
        
    def test_notthere(self):
        try:
            appfilepath('not_there.txt')
        except ProgrammingError, e:
            self.assertEqual( 'could not locate "not_there.txt" in any application', str(e))
        else:
            self.fail('excpected exception for file not found')
        
    def test_foundinsecond(self):
        self.assertEqual( appfilepath('found_in_second.txt',
                                      'templates/found_in_second.txt'),
                            path.join(app2_dir, 'templates', 'found_in_second.txt'))
    
    def test_directory(self):
        appfilepath('not_in_app1') == path.join(app2_dir, 'not_in_app1')
        
        
if __name__ == '__main__':
    #unittest.main()
    unittest.TextTestRunner().run(TestImports('test_callerglobals1'))
