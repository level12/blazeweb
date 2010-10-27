from os import path

from blazeutils.strings import reindent as bureindent
from blazeweb.globals import ag, settings
from blazeweb.hierarchy import findcontent, findfile, split_endpoint

def getcontent(__endpoint, *args, **kwargs):
    if '.' in __endpoint:
        c = TemplateContent(__endpoint)
    else:
        klass = findcontent(__endpoint)
        c = klass()
    c.process(args, kwargs)
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

    def process(self, args, kwargs):
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

    def __init__(self, endpoint):
        component, template = split_endpoint(endpoint)
        self.template = template
        self.endpoint = endpoint
        # the endpoint stack is used when the template engine's own
        # "include" is used.  It puts the included endpoint on the stack
        # which allows the include_css() and include_js() functions to
        # correctly determine the name of the file that is trying to be
        # included.
        self.endpoint_stack = []
        Content.__init__(self)

    def settype(self):
        basename, ext = path.splitext(self.template)
        self.primary_type = ext_registry[ext.lstrip('.')]

    def create(self, **kwargs):
        self.update_context(kwargs)
        return ag.tplengine.render_template(self.endpoint, kwargs)

    def update_context(self, context):
        context.update({
            'include_css': self.include_css,
            'include_js': self.include_js,
            'getcontent': self.include_content,
            'include_content': self.include_content,
            'include_html': self.include_html,
            'page_css': self.page_css,
            'page_js': self.page_js,
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

    def page_css(self, reindent=8):
        css = self.get('text/css', join_with='\n\n')
        if reindent:
            css = bureindent(css, 8)
        return ag.tplengine.mark_safe(css)

    def page_js(self, reindent=8):
        js = self.get('text/javascript')
        if reindent:
            js = bureindent(js, reindent)
        return ag.tplengine.mark_safe(js)

ext_registry = {
    'txt': 'text/plain',
    'htm': 'text/htm',
    'html': 'text/html',
    'css': 'text/css',
    'js': 'text/javascript'
}
