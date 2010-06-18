"""
This needs to go in its own mode so that we can avoid any pysmvt imports unless
the plugin is active.  This helps with test coverage of pysmvt.
"""

import os

import nose.plugins
from pysutils import tolist

class InitAppPlugin(nose.plugins.Plugin):
    opt_app_profile = 'pysmvt_profile'
    val_app_profile = None
    opt_app_name = 'pysmvt_name'
    val_app_name = None
    opt_disable = 'pysmvt_disable'
    val_disable = False
    opt_debug = 'pysmvt_debug'
    val_debug = False

    def add_options(self, parser, env=os.environ):
        """Add command-line options for this plugin"""
        env_opt = 'NOSE_WITH_%s' % self.name.upper()
        env_opt.replace('-', '_')

        parser.add_option("--pysmvt-profile",
                          dest=self.opt_app_profile, type="string",
                          default="Test",
                          help="The name of the test profile in settings.py"
                        )

        parser.add_option("--pysmvt-app_package",
                          dest=self.opt_app_name, type="string",
                          help="The name of the application's package, defaults"
                          " to top package of current working directory"
                        )

        parser.add_option("--pysmvt-disable",
                          dest=self.opt_disable,
                          action="store_true",
                          help="Disable plugin"
                        )

        parser.add_option("--pysmvt-debug",
                          dest=self.opt_debug,
                          action="store_true",
                          help="Disable plugin"
                        )

    def configure(self, options, conf):
        """Configure the plugin"""
        self.val_disable = getattr(options, self.opt_disable, False)
        if self.val_disable:
            return

        # import here so we can avoid test coverage issues
        from pysmvt import ag, settings
        from pysmvt.hierarchy import findobj
        from pysmvt.scripting import load_current_app, UsageError

        if hasattr(options, self.opt_app_profile):
            self.val_app_profile = getattr(options, self.opt_app_profile)
        if hasattr(options, self.opt_app_name) and getattr(options, self.opt_app_name):
            self.val_app_name = getattr(options, self.opt_app_name)
        try:
            _, _, _, wsgiapp = load_current_app(self.val_app_name, self.val_app_profile)

            # make the app available to the tests
            ag.wsgi_test_app = wsgiapp

            # an application can define functions to be called after the app
            # is initialized but before any test inspection is done or tests
            # are ran.  We call those functions here:
            for callstring in tolist(settings.testing.init_callables):
                tocall = findobj(callstring)
                tocall()
        except UsageError, e:
            if options.pysmvt_debug:
                raise
            self.val_disable = True
