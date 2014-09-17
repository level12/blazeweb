from os import path
import sys

from blazeutils.strings import reindent as bureindent
from blazeutils.rst import rst2html
from webhelpers.html import HTML

from blazeweb.globals import ag, settings
from blazeweb.hierarchy import findcontent, findfile, split_endpoint
from blazeweb.routing import abs_static_url, static_url

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

class _PlaceHolder(object):
    def __init__(self, cobj, ident, type, join_on=u'\n\n'):
        self.cobj = cobj
        self.placeholder = u'<<<blazeweb.content.placeholder.{0}>>>'.format(ident)
        self.type = type
        self.reindent_level = None
        self.count = 0
        self.join_on = join_on

    def content(self):
        text = self.cobj.get(self.type, self.join_on)
        if self.reindent_level:
            text = bureindent(text, self.reindent_level)
            # trim off the first level of indentation so that its in the place
            # in the template where its inserted and not indented from that
            # place.
            text = text.lstrip()
        return text

    def substitute(self, text):
        if not self.count:
            return text
        ph_content = self.content()
        return text.replace(self.placeholder, ph_content, self.count)

class TemplateContent(Content):
    ext_registry = {
        'txt': 'text/plain',
        'htm': 'text/htm',
        'html': 'text/html',
        'css': 'text/css',
        'js': 'text/javascript',
    }

    def __init__(self, endpoint):
        component, template = split_endpoint(endpoint)
        self.template = template
        self.endpoint = endpoint
        self.css_ph = _PlaceHolder(self, 'css', 'text/css')
        self.js_ph = _PlaceHolder(self, 'js', 'text/javascript')
        self.link_tags_ph = _PlaceHolder(self, 'link_tags', 'x-link-tags', u'\n')
        self.script_tags_ph = _PlaceHolder(self, 'script_tags', 'x-script-tags', u'\n')

        # the endpoint stack is used when the template engine's own
        # "include" is used.  It puts the included endpoint on the stack
        # which allows the include_css() and include_js() functions to
        # correctly determine the name of the file that is trying to be
        # included.
        self.endpoint_stack = []

        Content.__init__(self)
        self.data = {
            'x-link-tags': [],
            'x-script-tags': [],
        }

    def settype(self):
        basename, ext = path.splitext(self.template)
        try:
            self.primary_type = self.ext_registry[ext.lstrip('.')]
        except KeyError:
            self.primary_type = 'text/plain'

    def create(self, **kwargs):
        self.update_context(kwargs)
        content = ag.tplengine.render_template(self.endpoint, kwargs)
        #if self.css_placeholder_count:
        #    css_content = self.page_css()
        #    template_content = template_content.replace(
        #            self.css_placeholder, css_content, self.css_placeholder_count)
        #if self.js_placeholder_count:
        #    js_content = self.page_js()
        #    template_content = template_content.replace(
        #            self.js_placeholder, js_content, self.js_placeholder_count)
        #if self.script_tags_placeholder_count:
        #    js_tags_content = self.page_js()
        #    template_content = template_content.replace(
        #            self.js_placeholder, js_content, self.js_placeholder_count)
        content = self.css_ph.substitute(content)
        content = self.js_ph.substitute(content)
        content = self.link_tags_ph.substitute(content)
        content = self.script_tags_ph.substitute(content)
        return content

    def update_context(self, context):
        context.update({
            'include_css': self.include_css,
            'include_js': self.include_js,
            'include_rst': self.include_rst,
            'include_mkdn': self.include_mkdn,
            'getcontent': self.include_content,
            'include_content': self.include_content,
            'include_html': self.include_html,
            'page_css': self.page_css_ph,
            'page_js': self.page_js_ph,
            'link_css_url': self.link_css_url,
            'source_js_url': self.source_js_url,
            'head_link_tags': self.head_link_tags_ph,
            'head_script_tags': self.head_script_tags_ph,
            '__TemplateContent.endpoint_stack': self.endpoint_stack,
            '__TemplateContent.obj': self
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

    def head_link_tags_ph(self, reindent=4):
        ph = self.link_tags_ph
        ph.count += 1
        ph.reindent_level = reindent
        return ag.tplengine.mark_safe(ph.placeholder)

    def head_script_tags_ph(self, reindent=4):
        ph = self.script_tags_ph
        ph.count += 1
        ph.reindent_level = reindent
        return ag.tplengine.mark_safe(ph.placeholder)

    def page_css_ph(self, reindent=8):
        ph = self.css_ph
        ph.count += 1
        ph.reindent_level = reindent
        return ag.tplengine.mark_safe(ph.placeholder)

    def page_js_ph(self, reindent=8):
        ph = self.js_ph
        ph.count += 1
        ph.reindent_level = reindent
        return ag.tplengine.mark_safe(ph.placeholder)

    def link_css_url(self, url, **kwargs):
        if not kwargs.pop('relative_path', False):
            url = abs_static_url(url)
        else:
            url = static_url(url)
        link_tag = HTML.link(rel='stylesheet', type='text/css', href=url, **kwargs)
        self.data['x-link-tags'].append(link_tag)
        return u''

    def source_js_url(self, url, **kwargs):
        if not kwargs.pop('relative_path', False):
            url = abs_static_url(url)
        else:
            url = static_url(url)
        script_tag = HTML.script(type='text/javascript', src=url, **kwargs)
        self.data['x-script-tags'].append(script_tag)
        return u''
