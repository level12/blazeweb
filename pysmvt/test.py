import os
import nose.plugins
from pysmvt import config

class PysmvtPlugin(nose.plugins.Plugin):
    enabled = False
    name = 'pysmvt'
    appnameopt = 'pysmvt_appname'
    appprofileopt = 'pysmvt_profile'
    appname = ''
    appprofile = ''
    
    def add_options(self, parser, env=os.environ):
        """Add command-line options for this plugin"""
        env_opt = 'NOSE_WITH_%s' % self.name.upper()
        env_opt.replace('-', '_')

        parser.add_option("--%s-app" % self.name,
                          dest=self.appnameopt, type="string",
                          default="",
                          help="The name of the pysmvt application to test"
                        )

        parser.add_option("--%s-profile" % self.name,
                          dest=self.appprofileopt, type="string",
                          default="Test",
                          help="The name of the test profile in settings.py"
                        )
    
    def configure(self, options, conf):
        """Configure the plugin"""
        if hasattr(options, self.appnameopt):
            self.enabled = bool(getattr(options, self.appnameopt))
            self.appname = getattr(options, self.appnameopt)
        if hasattr(options, self.appprofileopt):
            self.appprofile = getattr(options, self.appprofileopt)

    def begin(self):
        appsmod = __import__('%s.applications' % self.appname, globals(), locals(), [''])
        self.consoleapp = appsmod.make_console(self.appprofile)
        
    def beforeTest(self, test):
        self.consoleapp.start_request()
    
    def afterTest(self, test):
        self.consoleapp.end_request()