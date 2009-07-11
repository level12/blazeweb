"""
    == Making The Plugins Available ==
    
    If pysmvt is installed, you should see the following in the output of
    `nosetests --help`:
    
        ...
        --add-pkg-tests=PYSMVT_PKGTESTS
                    A comma separated list of packages from which tests
                    should be gathered
        --app-profile=PYSMVT_PROFILE
                    The name of the test profile in settings.py
        ...
    
    == Using the Plugins ==
    
    You **must** be inside a pysmvt application's package directory for
    these plugins to work:
    
        `cd .../myproject/src/myapp-dist/myapp/`
    
    === Tests From Package Plugin ===
    
    Allows one to run tests from another package. Useful when you are
    running tests for an application but also want to run tests on
    supporting applications that are not under the current working
    directory. For example, in order to run the tests for pysapp, from the
    pysappexample application (because an application is required for some
    of the pysapp functional tests), you would run:
    
        `cd .../myproject/src/pysappexample-dist/pysappexample/`
        `nosetests --add-pkg-tests=pysapp`
    
    This will run all the tests in pysappexample as well as pysapp. If you
    are going to do this kind of thing a lot, there is an easier way.  See
    the next section.
    
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
        
        `nosetests  --app-profile=mytestprofile`
        
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
        
        `nosetests  --app-profile=testpysapp`
    
    Would be equivelent to running:
    
        `nosetests --add-pkg-tests=pysapp`
    
    Packages can also be specified as a list/tuple:
        
        # include multiple tests
        self.testing.include_pkgs = ('pysapp', 'somepkg')        
"""

import os
import nose.plugins
from pysmvt import config, ag, settings
from pysmvt.script import _app_name
from pysutils import tolist

class InitCurrentAppPlugin(nose.plugins.Plugin):
    enabled = False
    app_pkg_name = None
    opt_app_profile = 'pysmvt_profile'
    val_app_profile = None
    
    def add_options(self, parser, env=os.environ):
        """Add command-line options for this plugin"""
        env_opt = 'NOSE_WITH_%s' % self.name.upper()
        env_opt.replace('-', '_')

        parser.add_option("--app-profile",
                          dest=self.opt_app_profile, type="string",
                          default="Test",
                          help="The name of the test profile in settings.py"
                        )
    
    def configure(self, options, conf):
        """Configure the plugin"""
        self.app_pkg_name = _app_name()
        self.enabled = bool(self.app_pkg_name)
        if hasattr(options, self.opt_app_profile):
            self.val_app_profile = getattr(options, self.opt_app_profile)

    def begin(self):
        apps_pymod = __import__('%s.applications' % self.app_pkg_name, globals(), locals(), [''])
        ag._wsgi_test_app = apps_pymod.make_wsgi(self.val_app_profile)
    
    def loadTestsFromNames(self, names, module=None):
        try:
            names.extend(tolist(settings.testing.include_pkgs))
        except AttributeError, e:
            if "has no attribute 'testing'" not in str(e):
                raise

class TestsFromPackagePlugin(nose.plugins.Plugin):
    enabled = False
    name = 'pkgtests'
    opt_name = 'pysmvt_pkgtests'
    opt_value = None
    
    def add_options(self, parser, env=os.environ):
        """Add command-line options for this plugin"""
        env_opt = 'NOSE_WITH_%s' % self.name.upper()
        env_opt.replace('-', '_')

        parser.add_option("--add-pkg-tests",
                          dest=self.opt_name, type="string",
                          default="",
                          help="A comma separated list of packages from which "\
                            "tests should be gathered"
                        )

    def configure(self, options, conf):
        """Configure the plugin"""
        if hasattr(options, self.opt_name):
            self.enabled = bool(getattr(options, self.opt_name))
            self.opt_value = getattr(options, self.opt_name)

    def loadTestsFromNames(self, names, module=None):
        for pkgname in self.opt_value.split(','):
            names.append(pkgname)