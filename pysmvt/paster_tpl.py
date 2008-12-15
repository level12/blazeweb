from paste.script.templates import Template, var
from paste.util.template import paste_script_template_renderer
from paste.script import command

class DummyCommand(command.Command):
    simulate = False
    parser = command.Command.standard_parser()

class DummyOptions(object):
    simulate = False

def dummy_cmd(interactive, verbose, overwrite):
    cmd = DummyCommand('dummy')
    cmd.interactive = interactive
    cmd.verbose = verbose
    cmd.options = DummyOptions()
    cmd.options.overwrite = overwrite
    return cmd

class ProjectTemplate(Template):

    egg_plugins = ['pysmvt']
    summary = 'Template for creating a basic pysmvt project'
    _template_dir = ('pysmvt', 'paster_tpls/pysmvt')
    template_renderer = staticmethod(paste_script_template_renderer)
    summary = "A basic setuptools-enabled package"
    vars = [
        var('description', 'One-line description of the package'),
        var('author', 'Your name'),
        var('programmer_email', 'Your email'),
        ]
    
    def pre(self, command, output_dir, vars):
        # convert user's name into a username var
        author = vars['author']
        vars['username'] = author.split(' ')[0].capitalize()
        