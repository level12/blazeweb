"""
    == Making The Plugins Available ==
    
    If pysmvt is installed, you should see the following in the output of
    `nosetests --help`:
    
        ...
        --pysmvt-app-profile=PYSMVT_PROFILE
                    The name of the test profile in settings.py
        ...
    
    == Using the Plugins ==
    
    You **must** be inside a pysmvt application's package directory for
    these plugins to work:
    
        `cd .../myproject/src/myapp-dist/myapp/`
    
    === Init Current App Plugin ===
    
    This plugin does two things:
        
        - initializes a WSGI application for the current application
          (optionally allowing you to specify which profile you want used
          to initlize the application)
        - automatically includes test's from packages if so defined in the
          profile which is loaded.
    
    You don't have to do anything explicit to use this plugin.  It is
    enabled automatically when `nosetests` is run from inside an
    application's directory structure.  Assuming your make_wsgi() function
    is setup correctly, globaly proxy objects like 'ag' should now function
    correctly.  Request level objects, like 'rg' will not yet be available
    however.
    
    In order to get access to the wsgi application that was instantiated,
    you can do:
        
        from pysmvt import ag
        
        testapp = ag._wsgi_test_app
        
    `testapp` could now be used in the pysmvt.utils.wrapinapp() decorator.
    
    The default profile used with this plugin is 'Test'.  If you need to
    specifiy a different profile, do:
        
        `nosetests  --pymvt-app-profile=mytestprofile`
        
    To include tests from packges outside the application's directory
    structure, you can put a `testing.include_pkgs` attribute in your test
    profile. For example:
    
        class TestPysapp(Test):
            def __init__(self):
                # call parent init to setup default settings
                Test.__init__(self)
                
                # include pysapp tests
                self.testing.include_pkgs = 'pysapp'
        testpysapp = TestPysapp
    
    Running:
        
        `nosetests  --pysmvt-app-profile=testpysapp`
    
    Would be equivelent to running:
    
        `nosetests pysapp`
    
    Packages can also be specified as a list/tuple:
        
        # include multiple tests
        self.testing.include_pkgs = ('pysapp', 'somepkg')        
"""

import os
import nose.plugins
from pysmvt import ag, settings
from pysmvt.script import _app_name
from pysutils import tolist
from werkzeug import Client as WClient
from werkzeug import BaseRequest

class InitCurrentAppPlugin(nose.plugins.Plugin):
    opt_app_profile = 'pysmvt_profile'
    val_app_profile = None
    opt_app_name = 'pysmvt_name'
    val_app_name = None
    opt_disable = 'pysmvt_disable'
    val_disable = False
    
    def add_options(self, parser, env=os.environ):
        """Add command-line options for this plugin"""
        env_opt = 'NOSE_WITH_%s' % self.name.upper()
        env_opt.replace('-', '_')

        parser.add_option("--pysmvt-app-profile",
                          dest=self.opt_app_profile, type="string",
                          default="Test",
                          help="The name of the test profile in settings.py"
                        )
        
        parser.add_option("--pysmvt-app-name",
                          dest=self.opt_app_profile, type="string",
                          default="Test",
                          help="The name of the application's package, defaults"
                          " to top package of current working directory"
                        )
        
        parser.add_option("--pysmvt-disable",
                          dest=self.opt_disable,
                          action="store_true",
                          help="Disable plugin"
                        )
        
    def configure(self, options, conf):
        """Configure the plugin"""
        self.val_disable = getattr(options, self.opt_disable, False)
        if not self.val_disable:
            if hasattr(options, self.opt_app_profile):
                self.val_app_profile = getattr(options, self.opt_app_profile)
            if hasattr(options, self.opt_app_name):
                self.val_app_name = getattr(options, self.opt_app_name)
            else:
                try:
                    self.val_app_name = _app_name()
                except Exception, e:
                    if 'package name could not be determined' not in str(e):
                        raise
                if not self.val_app_name:
                    self.val_disable = True
        
        if not self.val_disable:
            apps_pymod = __import__('%s.applications' % self.val_app_name, globals(), locals(), [''])
            ag._wsgi_test_app = apps_pymod.make_wsgi(self.val_app_profile)

    def loadTestsFromNames(self, names, module=None):
        if not self.val_disable:
            try:
                names.extend(tolist(settings.testing.include_pkgs))
            except AttributeError, e:
                if "has no attribute 'testing'" not in str(e):
                    raise

class Client(WClient):
    
    def open(self, *args, **kwargs):
        """
            if follow_redirects is requested, a (BaseRequest, response) tuple
            will be returned, the request being the last redirect request
            made to get the response
        """
        fr = kwargs.get('follow_redirects', False)
        if fr:
            kwargs['as_tuple'] = True
        retval = WClient.open(self, *args, **kwargs)
        if fr:
            return BaseRequest(retval[0]), retval[1]
        return retval
