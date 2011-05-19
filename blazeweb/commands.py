from __future__ import with_statement
import os
from os import path

from blazeutils.helpers import pprint
from werkzeug.serving import run_simple
from werkzeug import Client, BaseResponse
from werkzeug.script import make_shell

from blazeweb.globals import ag, settings
from blazeweb.hierarchy import list_component_mappings
from blazeweb.paster_tpl import run_template
from blazeweb.tasks import run_tasks
from blazeweb.utils.filesystem import copy_static_files

import paste.script.command as pscmd

###
### BLAZEWEB COMMANDS FIRST
###
class ProjectCommand(pscmd.Command):

    summary = "Create a project layout using a pre-defined template"
    usage = "APP_NAME"
    group_name = ""

    min_args = 1
    max_args = 1

    parser = pscmd.Command.standard_parser(verbose=False)
    parser.add_option('-t', '--template',
                        dest='template',
                        default='bwproject',
                        help="The pre-defined template to use")
    parser.add_option('--no-interactive',
                      dest='interactive',
                      action='store_false',
                      default=True,)
    parser.add_option('--verbose',
                      dest='verbose',
                      action='store_true',
                      default=False)
    parser.add_option('--no-overwrite',
                      dest='overwrite',
                      action='store_false',
                      default=True)
    def command(self):
        projname = self.args[0]
        output_dir = path.join(os.getcwd(), '%s-dist' % projname)
        vars = {'project': projname,
                'package': projname,
                }
        run_template(
            self.options.interactive,
            self.options.verbose,
            self.options.overwrite,
            vars,
            output_dir,
            self.options.template,
            'blazeweb_project_template'
        )

###
### Now Application Specific Commands
###
class ServeCommand(pscmd.Command):
        # Parser configuration
        summary = "Serve the application by starting a development http server"
        usage = ""

        parser = pscmd.Command.standard_parser(verbose=False)
        parser.add_option('-a', '--address',
                        dest='address',
                        default='localhost',
                        help="IP address or hostname to serve from")
        parser.add_option('-P', '--port',
                        dest='port',
                        default=5000,
                        type='int')
        parser.add_option('--no-reloader',
                      dest='reloader',
                      action='store_false',
                      default=True,)
        parser.add_option('--with-debugger',
                      dest='debugger',
                      action='store_true',
                      default=False,)
        parser.add_option('--with-evalex',
                      dest='evalex',
                      action='store_true',
                      default=False,)
        parser.add_option('--with-threaded',
                      dest='threaded',
                      action='store_true',
                      default=False,)
        parser.add_option('--processes',
                        dest='processes',
                        default=1,
                        type='int',
                        help='number of processes to use')
        parser.add_option('--reloader-interval',
                        dest='reloader_interval',
                        default=1,
                        type='int',)
        parser.add_option('--pass-through-errors',
                      dest='pass_through_errors',
                      action='store_true',
                      default=False,)

        def command(self):
            if settings.logs.enabled:
                # our logging conflicts with werkzeug's, see issue #13
                # this is to give some visual feedback that the server did in fact start
                print ' * Serving on http://%s:%s/' % (self.options.address, self.options.port)
            run_simple(
                self.options.address,
                self.options.port,
                self.wsgiapp,
                use_reloader = self.options.reloader,
                use_debugger = self.options.debugger,
                use_evalex = self.options.evalex,
                extra_files = None,
                reloader_interval = self.options.reloader_interval,
                threaded = self.options.threaded,
                processes = self.options.processes,
                passthrough_errors = self.options.pass_through_errors,
            )

class TestRunCommand(pscmd.Command):
        # Parser configuration
        summary = "runs a single request through the application"
        usage = "URL"

        min_args = 0
        max_args = 1

        parser = pscmd.Command.standard_parser(verbose=False)
        parser.add_option('--silent',
                      dest='silent',
                      action='store_true',
                      default=False,)
        parser.add_option('--no-headers',
                      dest='show_headers',
                      action='store_false',
                      default=True,)
        parser.add_option('--no-body',
                      dest='show_body',
                      action='store_false',
                      default=True,)

        def command(self):
            options = self.options
            c = Client(self.wsgiapp, BaseResponse)
            if self.args:
                url = self.args[0]
            else:
                url = '/'
            resp = c.get(url)

            if options.show_headers and not options.silent:
                print resp.status
                print resp.headers

            if options.show_body and not options.silent:
                for respstr in resp.response:
                    print respstr

class TasksCommand(pscmd.Command):
        # Parser configuration
        summary = "runs task(s)"
        usage = "TASK [TASK [TASK [...]]]"

        min_args = 1

        parser = pscmd.Command.standard_parser(verbose=False)
        parser.add_option('-t', '--test-only',
                      dest='test_only',
                      action='store_true',
                      default=False,)

        def command(self):
            run_tasks(self.args, test_only=self.options.test_only)

class ShellCommand(pscmd.Command):
        # Parser configuration
        summary = "run a shell with an application initialized"
        usage = ""

        min_args = 0
        max_args = 0

        parser = pscmd.Command.standard_parser(verbose=False)
        parser.add_option('--ipython',
                      dest='use_ipython',
                      action='store_true',
                      default=False,
                      help='use IPython')

        def command(self):
            # set what will already be in the namespace for the shell.  Saves us from
            # typing common import statements
            shell_namespace = {
                'ag': ag._current_obj(),
                'settings': settings._current_obj()
            }
            shell_act = make_shell(lambda: shell_namespace, 'blazeweb Interactive Shell')
            shell_act(self.options.use_ipython)

class RoutesCommand(pscmd.Command):
        # Parser configuration
        summary = "prints out all routes configured for the application"
        usage = ""

        min_args = 0
        max_args = 0

        parser = pscmd.Command.standard_parser(verbose=False)
        parser.add_option('-e', '--show-endpoints',
                      dest='show_endpoints',
                      action='store_true',
                      default=False,
                      help='Shows the mapped URL as well as the endpoint')

        def command(self):
            toprint = []
            for rule in ag.route_map.iter_rules():
                if self.options.show_endpoints:
                    toprint.append((rule.rule, rule.endpoint))
                else:
                    toprint.append(rule.rule)
            pprint(toprint)

class StaticCopyCommand(pscmd.Command):
        # Parser configuration
        summary = "copy's app and component static files to the designated location"
        usage = ""

        min_args = 0
        max_args = 0

        parser = pscmd.Command.standard_parser(verbose=False)
        parser.add_option('-d', '--delete-existing',
                      dest='delete_existing',
                      action='store_true',
                      default=False,
                      help='Delete "app" and "component" directories in the destination if they exist')

        def command(self):
            copy_static_files(delete_existing=self.options.delete_existing)
            print '\n - files/dirs copied succesfully\n'

import re
class JinjaConvertCommand(pscmd.Command):
        # Parser configuration
        summary = "convert jinja delimiters from old style to new style"
        usage = ""

        min_args = 0
        max_args = 0

        parser = pscmd.Command.standard_parser(verbose=False)

        def change_tags(self, contents):
            contents = re.sub('<{', '{{', contents)
            contents = re.sub('<%', '{%', contents)
            contents = re.sub('<#', '{#', contents)
            contents = re.sub('}>', '}}', contents)
            contents = re.sub('%>', '%}', contents)
            contents = re.sub('#>', '#}', contents)
            return contents

        def command(self):
            print 'converting:'
            cwd = os.getcwd()
            for fname in os.listdir(cwd):
                if not fname.endswith('.html'):
                    continue
                with open(fname, 'r') as fh:
                    contents = fh.read().decode('utf-8')
                contents = self.change_tags(contents)
                with open(fname, 'w') as fh:
                    fh.write(contents.encode('utf-8'))
                print '    %s' % fname

class ComponentMapCommand(pscmd.Command):
    # Parser configuration
    summary = "List the component map"
    usage = ""

    min_args = 0
    max_args = 0

    parser = pscmd.Command.standard_parser(verbose=False)

    def command(self):
        pprint(list_component_mappings(inc_apps=True))
