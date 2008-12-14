import config
import unittest

import pysmvttestapp.applications
import pysmvt.config
from pysmvt import appimport, modimport, modimportauto, appimportauto
from pysmvt.application import Application
import pysmvttestapp.settings

class TestImports(unittest.TestCase):
    def setUp(self):
        self.app = pysmvttestapp.applications.make_console('Testruns')
        self.app.start_request()
        self.todelete = []
        self.globals_len = len(globals())
        
    def tearDown(self):
        self.app.end_request()
        self.app = None
        for key in self.todelete:
            del(globals()[key])
        self.todelete = None
        if self.globals_len != len(globals()):
            self.fail('leftovers in globals')
        
    def test_imp1(self):
        m = __import__('pysmvttestapp.settings', fromlist=[''])
        self.assertEqual( m, pysmvttestapp.settings )

    def test_imp2(self):
        """ application level import """
        self.assertEqual( __import__('pysmvttestapp.imptests', fromlist=['']) ,
                         appimport('imptests'))
    
        # now try a single from item
        imptests = __import__('pysmvttestapp.imptests', fromlist=['obj1'])
        obj1 = imptests.obj1
        obj2 = imptests.obj2
        self.assertEqual(obj1, appimport('imptests', 'obj1'))
        
        # now try multiple from items
        self.assertEqual([obj1, obj2], appimport('imptests', ['obj1', 'obj2']))
        
    def test_imp3(self):
        """ application level import from supporting app """
        self.assertEqual( __import__('pysmvttestapp2.base', fromlist=['']) ,
                         appimport('base'))
        
        # now try items from across different apps in the same from list
        imptests = __import__('pysmvttestapp.imptests', fromlist=['obj1'])
        imptests2 = __import__('pysmvttestapp2.imptests', fromlist=['obj2'])
        obj1 = imptests.obj1
        obj2 = imptests.obj2
        obj3 = imptests2.obj3
        self.assertEqual([obj1, obj2, obj3],
            appimport('imptests', ['obj1', 'obj2', 'obj3']))
    
    def test_callerglobals1(self):
        self.todelete.append('imptests')
        i_imptests = __import__('pysmvttestapp.imptests', fromlist=[''])
        appimportauto('imptests')
        self.assertEqual(imptests, i_imptests)
    
    def test_callerglobals2(self):
        # all we are doing here is making sure our tests work.  We need to make
        # sure we don't leave stuff in globals() that might affect our tests
        # note: for this test, the name of the functions matter b/c
        # of how they are sorted
        try:
            print imptests
            self.fail('imptests should have thrown NameError')
        except NameError, e:
            assert "global name 'imptests' is not defined" == str(e)
     
    def test_callerglobals3(self):
        self.todelete.append('obj1')
         
        # now try a single from item
        imptests = __import__('pysmvttestapp.imptests', fromlist=['obj1'])
        imptests.obj1
        appimportauto('imptests', 'obj1')
        self.assertEqual(obj1, imptests.obj1)

    def test_callerglobals4(self):
        self.todelete.extend(['obj1', 'obj2'])
        # now try multiple from items
        imptests = __import__('pysmvttestapp.imptests', fromlist=['obj1'])
        appimportauto('imptests', ['obj1', 'obj2'])
        self.assertEqual([imptests.obj1, imptests.obj2], [obj1, obj2])
    
    def test_callerglobals5(self):
        self.todelete.extend(['obj1', 'obj2', 'obj3'])
        ## now try a items from across different apps in the same from list
        imptests = __import__('pysmvttestapp.imptests', fromlist=['obj1'])
        imptests2 = __import__('pysmvttestapp2.imptests', fromlist=['obj2'])
        appimportauto('imptests', ['obj1', 'obj2', 'obj3'])
        self.assertEqual([imptests.obj1, imptests.obj2, imptests2.obj3], [obj1, obj2, obj3])
    
    def test_mod1(self):
        """ module level import """
        self.assertEqual( __import__('pysmvttestapp.modules.tests.imptests', fromlist=['']) ,
                         modimport('tests.imptests'))
    
        # now try a single from item
        imptests = __import__('pysmvttestapp.modules.tests.imptests', fromlist=['obj1'])
        obj1 = imptests.obj1
        self.assertEqual(obj1, modimport('tests.imptests', 'obj1'))
        
        # now try multiple from items
        obj2 = imptests.obj2
        self.assertEqual([obj1, obj2], modimport('tests.imptests', ['obj1', 'obj2']))
        
    def test_mod2(self):
        """ module level import from supporting app """
        self.assertEqual( __import__('pysmvttestapp2.modules.tests.base', fromlist=['']) ,
                         modimport('tests.base'))
        
        # now try items from across different apps in the same from list
        imptests = __import__('pysmvttestapp.modules.tests.imptests', fromlist=['obj1'])
        imptests2 = __import__('pysmvttestapp2.modules.tests.imptests', fromlist=['obj2'])
        obj1 = imptests.obj1
        obj2 = imptests.obj2
        obj3 = imptests2.obj3
        self.assertEqual([obj1, obj2, obj3],
            modimport('tests.imptests', ['obj1', 'obj2', 'obj3']))

    def test_badimports(self):
        try:
            appimport('nothere')
        except ImportError, e:
            self.assertEqual(str(e), 'cannot import "nothere" from any application')
        
        try:
            appimport('nothere', 'obj1')
        except ImportError, e:
            self.assertEqual(str(e), 'cannot import "nothere" with attribute "obj1" from any application')
        
        try:
            modimport('tests.nothere')
        except ImportError, e:
            self.assertEqual(str(e), 'cannot import "modules.tests.nothere" from any application')
    
    def test_module_then_list(self):
        """ getting module first should not affect attribute import later """
        self.assertEqual( __import__('pysmvttestapp.imptests', fromlist=['']) ,
                         appimport('imptests'))
        
        # now try items from across different apps in the same from list
        imptests = __import__('pysmvttestapp.imptests', fromlist=['obj1'])
        imptests2 = __import__('pysmvttestapp2.imptests', fromlist=['obj2'])
        obj1 = imptests.obj1
        obj3 = imptests2.obj3
        self.assertEqual([obj1, obj3],
            appimport('imptests', ['obj1', 'obj3']))
    
    def test_list_only(self):
        # don't load any modules first
        appimport('imptests', ('obj3', 'obj1'))
        # do a second run to make sure the cache is being pulled from
        appimport('imptests', ('obj3', 'obj1'))
        
if __name__ == '__main__':
    #unittest.main()
    unittest.TextTestRunner().run(TestImports('test_callerglobals1'))
