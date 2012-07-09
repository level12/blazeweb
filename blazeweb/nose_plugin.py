"""
This needs to go in its own module so that we can avoid any blazeweb imports unless
the plugin is active.  This helps with test coverage of blazeweb.
"""

import os

import nose.plugins
from blazeutils import tolist

class InitAppPlugin(nose.plugins.Plugin):
    enabled = True
    opt_app_profile = 'blazeweb_profile'
    val_app_profile = None
    opt_app_name = 'blazeweb_name'
    val_app_name = None
    opt_disable = 'blazeweb_disable'
    val_disable = False
    opt_debug_name = 'blazeweb_debug'
    val_debug = False

    def options(self, parser, env=os.environ):
        """Add command-line options for this plugin"""
        env_opt = 'NOSE_WITH_%s' % self.name.upper()
        env_opt.replace('-', '_')

        parser.add_option("--blazeweb-profile",
                          dest=self.opt_app_profile, type="string",
                          default="Test",
                          help="The name of the test profile in settings.py"
                        )

        parser.add_option("--blazeweb-package",
                          dest=self.opt_app_name, type="string",
                          help="The name of the application's package, defaults"
                          " to top package of current working directory"
                        )

        parser.add_option("--blazeweb-disable",
                          dest=self.opt_disable,
                          action="store_true",
                          help="Disable plugin"
                        )

        parser.add_option("--blazeweb-debug",
                          dest=self.opt_debug_name,
                          action="store_true",
                          help="plugin will raise exceptions rather then disabling itself"
                        )

    def configure(self, options, config):
        """Configure the plugin"""
        nose.plugins.Plugin.configure(self, options, config)

        self.val_disable = getattr(options, self.opt_disable, False)
        if self.val_disable:
            self.enabled = False

        if hasattr(options, self.opt_app_profile):
            self.val_app_profile = getattr(options, self.opt_app_profile)
        if hasattr(options, self.opt_app_name) and getattr(options, self.opt_app_name):
            self.val_app_name = getattr(options, self.opt_app_name)
        if hasattr(options, self.opt_debug_name) and getattr(options, self.opt_debug_name):
            self.val_debug = getattr(options, self.opt_debug_name)

    def begin(self):
        if self.val_disable:
            return
        # import here so we can avoid test coverage issues
        from blazeweb.events import signal
        from blazeweb.globals import ag, settings
        from blazeweb.hierarchy import findobj
        from blazeweb.scripting import load_current_app, UsageError

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

            # we also support events for pre-test setup
            signal('blazeweb.pre_test_init').send()
        except UsageError, e:
            if self.val_debug:
                raise
            self.val_disable = True
