import pkg_resources
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

    summary = 'Template for creating a basic pysmvt project'
    _template_dir = ('pysmvt', 'paster_tpls/project')
    template_renderer = staticmethod(paste_script_template_renderer)
    vars = [
        var('description', 'One-line description of the package'),
        var('author', 'Your name'),
        var('programmer_email', 'Your email'),
        ]
    
    def pre(self, command, output_dir, vars):
        # convert user's name into a username var
        author = vars['author']
        vars['username'] = author.split(' ')[0].capitalize()

class ModuleTemplate(Template):

    _template_dir = ('pysmvt', 'paster_tpls/module')
    template_renderer = staticmethod(paste_script_template_renderer)
    summary = "A pysmvt application module"
    
    def post(self, command, output_dir, vars):
        print ''
        print '-'*70
        print 'Action Required: enabled module in settings.py'
        print '-'*70
        print 'self.modules.%s.enabled = True' % vars['modname']

def run_template(interactive, verbose, overwrite, vars,
                 output_dir, tname, type):
    cmd = dummy_cmd(interactive, verbose, overwrite)
    templates = []
    extend_templates(templates, tname, type)
    
    # get rid of the name, object tuple
    templates = [tmpl for name, tmpl in templates]
    
    # check vars on template and required templates
    for template in templates[::-1]:
        vars = template.check_vars(vars, cmd)
    
    # run the template
    for template in templates:
        template.run(cmd, output_dir, vars)

def extend_templates(templates, tmpl_name, type):
    if '#' in tmpl_name:
        dist_name, tmpl_name = tmpl_name.split('#', 1)
    else:
        dist_name, tmpl_name = None, tmpl_name
    if dist_name is None:
        for entry in all_entry_points(type):
            if entry.name == tmpl_name:
                tmpl = entry.load()(entry.name)
                dist_name = entry.dist.project_name
                break
        else:
            raise LookupError(
                'Template by name %r not found' % tmpl_name)
    else:
        dist = pkg_resources.get_distribution(dist_name)
        entry = dist.get_entry_info(
            'pysmvt.%s'%type, tmpl_name)
        tmpl = entry.load()(entry.name)
    full_name = '%s#%s' % (dist_name, tmpl_name)
    for item_full_name, item_tmpl in templates:
        if item_full_name == full_name:
            # Already loaded
            return
    for req_name in tmpl.required_templates:
        extend_templates(templates, req_name, type)
    templates.append((full_name, tmpl))
    
def all_entry_points(type):
    return list(pkg_resources.iter_entry_points('pysmvt.%s'%type))