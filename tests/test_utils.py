import unittest
import os
import os.path as path
import rcsutils
import config

# setup the virtual environment so that we can import specific versions
# of system libraries but also ensure that our pysmvt module is what
# we are pulling from
rcsutils.setup_virtual_env('pysmvt-libs-trunk', __file__, '..')

from pysmvt import application
from pysmvt.utils import QuickSettings, pprint, ModulesSettings

class Base(QuickSettings):
    
    def __init__(self):
        QuickSettings.__init__(self)
        
        # name of the website/application
        self.name.full = 'full'
        self.name.short = 'short'
        
        # application modules from our application or supporting applications
        self.modules = ModulesSettings()
        self.modules.users.enabled = True
        self.modules.apputil.enabled = True
        self.modules.inactivemod.enabled = False
        
        #######################################################################
        # ROUTING
        #######################################################################
        # default routes
        self.routing.routes = [1, 2]
        
        # route prefix
        self.routing.prefix = ''
        
        #######################################################################
        # DATABASE
        #######################################################################
        self.db.echo = False
        
        #######################################################################
        # SESSIONS
        #######################################################################
        #beaker session options
        #http://wiki.pylonshq.com/display/beaker/Configuration+Options
        self.beaker.type = 'dbm'
        self.beaker.data_dir = 'session_cache'

        #######################################################################
        # TEMPLATE & VIEW
        #######################################################################
        self.template.default = 'default.html'
        self.template.admin = 'admin.html'
        self.trap_view_exceptions = True
        
        #######################################################################
        # LOGGING & DEBUG
        #######################################################################
        # currently support 'debug' & 'info'
        self.logging.levels = ()
        
        # no more values can be added
        self.lock()
        
class Default(Base):

    def __init__(self):
        Base.__init__(self)
        
        # supporting applications
        self.supporting_apps = ['rcsappbase']
        
        # application modules from our application or supporting applications
        self.unlock()
        self.modules.contentbase.enabled = True
        self.modules.lagcontent.enabled = True
        self.lock()
        
        #######################################################################
        # ROUTING
        #######################################################################
        self.routing.routes.extend([3,4])
        
        #######################################################################
        # DATABASE
        #######################################################################
        self.db.echo = True
        
        #######################################################################
        # LOGGING & DEBUG
        #######################################################################
        self.logging.levels = ('info', 'debug')
        self.trap_view_exceptions = False
        self.hide_exceptions = False

class TestQuickSettings(unittest.TestCase):

    def test_level1(self):
        es = QuickSettings()
        es.a = 1
        assert es.a == 1
        
    def test_level2(self):
        es = QuickSettings()
        es.a.a = 1
        assert es.a.a == 1
        
    def test_email(self):
        es = QuickSettings()
        es.email.smtp.server = 'example.com'
        es.email.smtp.user_name = 'myself'
        es.email.smtp.password = 'pass'
        
        assert es.email.smtp.server == 'example.com'
        assert es.email.smtp.user_name == 'myself'
        assert es.email.smtp.password == 'pass'
        
    def test_settings(self):
        s = Default()
        
        assert s.name.full == 'full'
        assert s.name.short == 'short'
        assert s.modules.keys() == ['users', 'apputil','contentbase', 'lagcontent']
        assert s.routing.routes == [1,2,3,4]
        
        assert s.db.echo == True
    
        assert s.logging.levels == ('info', 'debug')
        assert s.trap_view_exceptions == False
        assert s.hide_exceptions == False
        
        assert s.template.default == 'default.html'
        assert s.template.admin == 'admin.html'
        
        assert s.beaker.type == 'dbm'
        assert s.beaker.data_dir == 'session_cache'

    def test_lock(self):
        s = Default()
        
        try:
            foo = s.not_there
        except AttributeError, e:
            assert str(e) == "object has no attribute 'not_there' (object is locked)"
        else:
            self.fail("lock did not work, expected AttributeError")
        
        # make sure lock went to children
        try:
            foo = s.db.not_there
        except AttributeError, e:
            assert str(e) == "object has no attribute 'not_there' (object is locked)"
        else:
            self.fail("lock did not work on child, expected AttributeError")

    def test_unlock(self):
        s = Default()
        s.unlock()
        
        s.new_attr = 'new_attr'
        s.db.new_attr = 'new_attr'
        
        assert s.db.new_attr == 'new_attr'
        assert s.new_attr == 'new_attr'
        
        s.lock()
        
        try:
            foo = s.not_there
        except AttributeError, e:
            assert str(e) == "object has no attribute 'not_there' (object is locked)"
        else:
            self.fail("lock did not work, expected AttributeError")
        
        # make sure lock went to children
        try:
            foo = s.db.not_there
        except AttributeError, e:
            assert str(e) == "object has no attribute 'not_there' (object is locked)"
        else:
            self.fail("lock did not work on child, expected AttributeError")
        
    def test_dict_convert(self):
        s = Default()
        
        # beaker would need a dictionary, so lets see if it works
        d = {
            'type' : 'dbm',
            'data_dir' : 'session_cache'
        }
        
        assert dict(s.beaker) == d
        assert s.beaker.todict() == d
    
    def test_modules(self):
        s = Default()
        
        s.unlock()
        try:
            s.modules.badmod = False
        except TypeError:
            pass
        else:
            self.fail('expected TypeError when non QuickSettings object assigned to ModulesSettings object')
        s.modules.fatfingeredmod.enabledd = True
        s.lock()
        
        mods = ['users', 'apputil', 'contentbase', 'lagcontent']
        allmods = ['users', 'apputil', 'inactivemod', 'contentbase', 'lagcontent', 'fatfingeredmod']
        self.assertEqual( mods, s.modules.keys() )
        self.assertEqual( allmods, s.modules.keys(showinactive=True) )
        
        self.assertEqual( len(mods), len([v for v in s.modules]))
        self.assertEqual( len(mods), len(s.modules))
        self.assertEqual( len(mods), len(s.modules.values()))
        self.assertEqual( len(allmods), len(s.modules.values(showinactive=True)))
        
        self.assertEqual( len(mods), len(s.modules.todict()))
        self.assertEqual( len(allmods), len(s.modules.todict(showinactive=True)))
        
        self.assertTrue( 'users' in s.modules)
        self.assertFalse( 'inactivemod' in s.modules)
        
if __name__ == '__main__':
    unittest.main()
