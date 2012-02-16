from __future__ import with_statement
import logging
from os import path

from jinja2 import Environment, TemplateNotFound, BaseLoader, \
    Template as j2Template, contextfilter
from jinja2.utils import Markup

from blazeweb.globals import settings
from blazeweb.hierarchy import FileNotFound, findfile, split_endpoint
import blazeweb.templating as templating

log = logging.getLogger(__name__)

class _RootRenderWrapper(object):

    def __init__(self, tpl_name, root_render_func):
        self.tpl_name = tpl_name
        self.root_render_func = root_render_func

    def __call__(self, context):
        endpoint_stack = context.get('__TemplateContent.endpoint_stack', [])
        endpoint_stack.append(self.tpl_name)
        for event in self.root_render_func(context):
            yield event
        endpoint_stack.pop()

    def __eq__(self, other):
        """
            when super() is used in a block, jinja's implimentation looks
            for the original render func in a list using list.index(), so we
            need to make our function look like the original for the equals
            operator
        """
        return other == self.root_render_func

class Template(j2Template):

    @classmethod
    def _from_namespace(cls, environment, namespace, globals):
        # wrap the main root_render_func to track the name of the template
        # that is being rendered
        namespace['root'] = _RootRenderWrapper(namespace['name'], namespace['root'])

        # also wrap the root rendering function for each of this template's
        # blocks, otherwise our include functions will not calculate the current
        # template's name correctly when inside a block that is replacing the
        # the block of a parent template
        for block_name, block_root_render_func in namespace['blocks'].iteritems():
            namespace['blocks'][block_name] = _RootRenderWrapper(namespace['name'], block_root_render_func)

        return j2Template._from_namespace(environment, namespace, globals)

class Translator(templating.EngineBase):

    def __init__(self):
        self.env = Environment(
            loader=self.create_loader(),
            **self.get_settings()
            )
        self.env.template_class = Template
        self.init_globals()
        self.init_filters()

    def create_loader(self):
        return HierarchyLoader()

    def get_settings(self):
        def guess_autoescape(template_name):
            if template_name is None or '.' not in template_name:
                return False
            ext = template_name.rsplit('.', 1)[1]
            return ext in ('html', 'htm', 'xml')
        jsettings = settings.jinja
        if isinstance(jsettings.autoescape, (list, tuple)):
            jsettings.autoescape = guess_autoescape
        return jsettings.todict()

    def init_globals(self):
        self.env.globals.update(self.get_globals())

    def init_filters(self):
        filters = self.get_filters()
        filters['content'] = content_filter
        self.env.filters.update(filters)

    def render_template(self, endpoint, context):
        self.update_context(context)
        return self.env.get_template(endpoint).render(context)

    def render_string(self, string, context):
        return self.env.from_string(string).render(context)

    def mark_safe(self, value):
        """ when a template has auto-escaping enabled, mark a value as safe """
        return Markup(value)

class HierarchyLoader(BaseLoader):
    """
        A modification of Jinja's FileSystemLoader to take into account
        the hierarchy.
    """

    def __init__(self, encoding=settings.default.charset):
        self.encoding = encoding

    def find_template_path(self, endpoint):
        # try module level first
        try:
            component, template = split_endpoint(endpoint)
            endpoint = path.join('templates', template)
            if component:
                endpoint = '%s:%s' % (component, endpoint)
            return findfile(endpoint)
        except FileNotFound:
            pass
        ## try app level second if module wasn't specified
        #try:
        #    if ':' not in template:
        #        endpoint = 'templates/%s' % template
        #    return findfile(endpoint)
        #except FileNotFound:
        #    pass

    def get_source(self, environment, endpoint):
        log.debug('get_source() processing: %s' % endpoint)
        fpath = self.find_template_path(endpoint)
        if not fpath:
            raise TemplateNotFound(endpoint)
        with open(fpath) as f:
            contents = f.read().decode(self.encoding)
        old = path.getmtime(fpath)
        return contents, fpath, lambda: path.getmtime(fpath) == old

@contextfilter
def content_filter(context, child_content):
    parent_content = context['__TemplateContent.obj']
    parent_content.update_nonprimary_from_content(child_content)
    return Markup(child_content.primary)
