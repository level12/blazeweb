import os
import sys

import paste.script.command as pscmd
import pkg_resources
import optparse

class ScriptingHelperBase(object):
    def __init__(self):
        self.setup_parser()
        self.monkey_patch()
    
    def setup_parser(self):
        if self.distribution_name:
            dist = pkg_resources.get_distribution(self.distribution_name)
            location = dist.location
        else:
            dist = '<unknown>'
            location = '<unknown>'

        python_version = sys.version.splitlines()[0].strip()
        
        parser = optparse.OptionParser(add_help_option=False,
                                       version='%s from %s (python %s)'
                                       % (dist, location, python_version),
                                       usage='%prog [global_options] COMMAND [command_options]')
        
        parser.disable_interspersed_args()
        
        parser.add_option(
            '-h', '--help',
            action='store_true',
            dest='do_help',
            help="Show this help message")
        
        self.parser = parser
    
    def monkey_patch(self):
        pscmd.get_commands = lambda: self.get_commands()
        pscmd.parser = self.parser
        
    def run(self, args=None):
        
        if (not args and
            len(sys.argv) >= 2
            and os.environ.get('_') and sys.argv[0] != os.environ['_']
            and os.environ['_'] == sys.argv[1]):
            # probably it's an exe execution
            args = ['exe', os.environ['_']] + sys.argv[2:]
        if args is None:
            args = sys.argv[1:]
        options, args = self.parser.parse_args(args)
        options.base_parser = self.parser
        commands = self.get_commands()
        if options.do_help:
            args = ['help'] + args
        if not args:
            args = ['help']
        command_name = args[0]
        if command_name not in commands:
            command = pscmd.NotFoundCommand
        else:
            command = commands[command_name].load()
        self.invoke(command, command_name, options, args[1:])
    
    def get_commands(self):
        commands = {}
        for p in pkg_resources.iter_entry_points(self.entry_point_name):
            commands[p.name] = p
        return commands
    
    def invoke(self, command, command_name, options, args):
        try:
            runner = command(command_name)
            self.modify_runner(runner, options)
            exit_code = runner.run(args)
        except pscmd.BadCommand, e:
            print e.message
            exit_code = e.exit_code
        sys.exit(exit_code)
    
    def modify_runner(self, runner, options):
        return runner

class PysmvtScriptingHelper(ScriptingHelperBase):
    def __init__(self):
        self.distribution_name = 'pysmvt'
        self.entry_point_name = 'pysmvt.no_app_command'
        ScriptingHelperBase.__init__(self)

class AppScriptingHelper(ScriptingHelperBase):
    def __init__(self, appfactory):
        self.distribution_name = None
        self.entry_point_name = 'pysmvt.app_command'
        ScriptingHelperBase.__init__(self)
        self.appfactory = appfactory
    
    def setup_parser(self):
        ScriptingHelperBase.setup_parser(self)
        self.parser.add_option(
        '-p', '--settings-profile',
        dest='settings_profile',
        help='Choose which settings profile to use with this command.'\
            ' If not given, the default will be used.')

    def modify_runner(self, runner, options):
        # instantiate the app
        profile = options.settings_profile
        if profile:
            try:
                self.wsgiapp = self.appfactory(profile)
            except AttributeError:
                raise pscmd.BadCommand('Error: could not find settings profile: %s' % profile)
        else:
            self.wsgiapp = self.appfactory()
        runner.wsgiapp = self.wsgiapp
        return runner
    
def application_entry(appfactory):
    AppScriptingHelper(appfactory).run()

def pysmvt_entry():
    PysmvtScriptingHelper().run()