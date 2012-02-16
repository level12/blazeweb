from os import path
import sys

from blazeutils.strings import reindent as bureindent
from blazeutils.rst import rst2html

from blazeweb.globals import ag, settings
from blazeweb.hierarchy import findcontent, findfile, split_endpoint

def getcontent(__endpoint, *args, **kwargs):
    if '.' in __endpoint:
        c = TemplateContent(__endpoint)
    else:
        klass = findcontent(__endpoint)
        c = klass()
    c.process(*args, **kwargs)
    return c

class Content(object):

    def __init__(self):
        self.supporting_content = {}
        # note: the charset is set on the Response object, so if you change
        # this value and send bytes back to a View, which sends them
        # back to the response object, the response object will interpret them
        # as utf-8.
        self.charset = settings.default.charset
        self.data = {}

    def settype(self):
        self.primary_type = 'text/plain'

    def process(self, *args, **kwargs):
        self.settype()
        content = self.create(*args, **kwargs)
        self.add_content(self.primary_type, content)

    def create(self):
        return u''

    def add_content(self, content, type):
        self.content.setdefault(type, [])
        self.content[type] = content

    def update_nonprimary_from_endpoint(self, __endpoint, *args, **kwargs):
        c = getcontent(__endpoint, *args, **kwargs)
        self.update_nonprimary_from_content(c)
        return c

    def update_nonprimary_from_content(self, c):
        for type, clist in c.data.iteritems():
            if type != self.primary_type:
                self.data.setdefault(type, [])
                self.data[type].extend(clist)

    def add_content(self, type, content):
        self.data.setdefault(type, [])
        self.data[type].append(content)

    @property
    def primary(self):
        return self.get(self.primary_type)

    def get(self, type, join_with=u''):
        try:
            return join_with.join(self.data[type])
        except KeyError:
            return u''

    def __unicode__(self):
        return self.primary

    def __str__(self):
        return self.primary.encode(self.charset)

class TemplateContent(Content):
    css_placeholder = '<<<blazeweb.content.placeholder.page_css>>>'
    js_placeholder = '<<<blazeweb.content.placeholder.page_css>>>'

    def __init__(self, endpoint):
        component, template = split_endpoint(endpoint)
        self.template = template
        self.endpoint = endpoint
        self.css_reindent_level = None
        self.js_reindent_level = None
        self.css_placeholder_count = 0
        self.js_placeholder_count = 0

        # the endpoint stack is used when the template engine's own
        # "include" is used.  It puts the included endpoint on the stack
        # which allows the include_css() and include_js() functions to
        # correctly determine the name of the file that is trying to be
        # included.
        self.endpoint_stack = []
        Content.__init__(self)

    def settype(self):
        basename, ext = path.splitext(self.template)
        try:
            self.primary_type = ext_registry[ext.lstrip('.')]
        except KeyError:
            self.primary_type = 'text/plain'

    def create(self, **kwargs):
        self.update_context(kwargs)
        template_content = ag.tplengine.render_template(self.endpoint, kwargs)
        if self.css_placeholder_count:
            css_content = self.page_css()
            template_content = template_content.replace(
                    self.css_placeholder, css_content, self.css_placeholder_count)
        if self.js_placeholder_count:
            js_content = self.page_js()
            template_content = template_content.replace(
                    self.js_placeholder, js_content, self.js_placeholder_count)
        return template_content

    def update_context(self, context):
        context.update({
            'include_css': self.include_css,
            'include_js': self.include_js,
            'include_rst': self.include_rst,
            'include_mkdn': self.include_mkdn,
            'getcontent': self.include_content,
            'include_content': self.include_content,
            'include_html': self.include_html,
            'page_css': self.page_css_placeholder,
            'page_js': self.page_js_placeholder,
            '__TemplateContent.endpoint_stack': self.endpoint_stack
        })

    def _supporting_endpoint_from_ext(self, extension):
        current_endpoint = self.endpoint_stack[-1]
        component, template = split_endpoint(current_endpoint)
        basename, _ = path.splitext(template)
        endpoint = '%s.%s' % (basename, extension)
        if component:
            endpoint = '%s:%s' % (component, endpoint)
        return endpoint

    def include_content(self, __endpoint, *args, **kwargs):
        c = self.update_nonprimary_from_endpoint(__endpoint, *args, **kwargs)
        return c.primary

    def include_html(self, __endpoint, *args, **kwargs):
        html = self.include_content(__endpoint, *args, **kwargs)
        return ag.tplengine.mark_safe(html)

    def include_content(self, __endpoint, *args, **kwargs):
        c = self.update_nonprimary_from_endpoint(__endpoint, *args, **kwargs)
        return c.primary

    def include_css(self, __endpoint=None, **kwargs):
        if __endpoint is None:
            __endpoint = self._supporting_endpoint_from_ext('css')
        self.update_nonprimary_from_endpoint(__endpoint)
        return u''

    def include_js(self, __endpoint=None, **kwargs):
        if __endpoint is None:
            __endpoint = self._supporting_endpoint_from_ext('js')
        self.update_nonprimary_from_endpoint(__endpoint)
        return u''

    def include_rst(self, __endpoint=None, *args, **kwargs):
        if __endpoint is None:
            __endpoint = self._supporting_endpoint_from_ext('rst')
        rst = TemplateContent(__endpoint).create(**kwargs)
        html = rst2html(rst)
        return ag.tplengine.mark_safe(html)

    def include_mkdn(self, __endpoint=None, *args, **kwargs):
        if __endpoint is None:
            __endpoint = self._supporting_endpoint_from_ext('mkdn')
        c = TemplateContent(__endpoint)
        rst = c.create(**kwargs)
        html = rst2html(rst)
        return ag.tplengine.mark_safe(html)

    def page_css_placeholder(self, reindent=8):
        self.css_placeholder_count += 1
        self.css_reindent_level = reindent
        return ag.tplengine.mark_safe(self.css_placeholder)

    def page_css(self):
        css = self.get('text/css', join_with='\n\n')
        if self.css_reindent_level:
            css = bureindent(css, self.css_reindent_level)
        return ag.tplengine.mark_safe(css)

    def page_js_placeholder(self, reindent=8):
        self.js_placeholder_count += 1
        self.js_reindent_level = reindent
        return ag.tplengine.mark_safe(self.js_placeholder)

    def page_js(self):
        js = self.get('text/javascript')
        if self.js_reindent_level:
            js = bureindent(js, self.js_reindent_level)
        return ag.tplengine.mark_safe(js)

ext_registry = {
    'txt': 'text/plain',
    'htm': 'text/htm',
    'html': 'text/html',
    'css': 'text/css',
    'js': 'text/javascript',
}
