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
from pysmvt.utils import QuickSettings, pprint

class Base(QuickSettings):
    
    def __init__(self):
        QuickSettings.__init__(self)
        
        # name of the website/application
        self.name.full = 'full'
        self.name.short = 'short'
        
        # application modules from our application or supporting applications
        self.modules = ['users', 'apputil']
        
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
        self.modules.extend(['contentbase', 'lagcontent'])
        
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
        assert s.modules == ['users', 'apputil','contentbase', 'lagcontent']
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
            assert str(e) == 'attribute not_there not found (object is locked)'
        else:
            self.fail("lock did not work, expected AttributeError")
        
        # make sure lock went to children
        try:
            foo = s.db.not_there
        except AttributeError, e:
            assert str(e) == 'attribute not_there not found (object is locked)'
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
        
if __name__ == '__main__':
    unittest.main()
