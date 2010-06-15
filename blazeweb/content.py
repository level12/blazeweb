from os import path

from blazeweb import ag, settings
from blazeweb.hierarchy import findcontent, findfile, split_endpoint

def getcontent(endpoint, *args, **kwargs):
    if '.' in endpoint:
        c = TemplateContent(endpoint)
    else:
        klass = findcontent(endpoint)
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

    def update_from_endpoint(self, endpoint):
        c = getcontent(endpoint)
        self.update_from_content(c)

    def update_from_content(self, c):
        for type, clist in c.data.iteritems():
            self.data.setdefault(type, [])
            self.data[type].extend(clist)

    def add_content(self, type, content):
        self.data.setdefault(type, [])
        self.data[type].append(content)

    @property
    def primary(self):
        return self.get(self.primary_type)

    def get(self, type):
        try:
            return u''.join(self.data[type])
        except KeyError:
            return u''

    def __unicode__(self):
        return self.primary

    def __str__(self):
        return self.primary.encode(self.charset)

class TemplateContent(Content):

    def __init__(self, endpoint):
        plugin, template = split_endpoint(endpoint)
        self.plugin = plugin
        self.template = template
        self.endpoint = endpoint
        Content.__init__(self)


    def settype(self):
        basename, ext = path.splitext(self.template)
        self.basename = basename
        self.primary_type = ext_registry[ext.lstrip('.')]

    def create(self, **kwargs):
        # circular import fun!!
        from blazeweb.templating import render_template
        self.update_context(kwargs)
        return render_template(self.endpoint, **kwargs)

    def update_context(self, context):
        context.update({
            'include_css': self.include_css,
            'include_js': self.include_js,
            'page_css': self.page_css,
            'page_js': self.page_js,
        })

    def _supporting_endpoint_from_ext(self, extension):
        endpoint = '%s.%s' % (self.basename, extension)
        if self.plugin:
            endpoint = '%s:%s' % (self.plugin, endpoint)
        return endpoint

    def include_css(self, endpoint=None, **kwargs):
        if endpoint is None:
            endpoint = self._supporting_endpoint_from_ext('css')
        self.update_from_endpoint(endpoint)
        return u''

    def include_js(self, endpoint=None, **kwargs):
        if endpoint is None:
            endpoint = self._supporting_endpoint_from_ext('js')
        self.update_from_endpoint(endpoint)
        return u''

    def page_css(self):
        return self.get('text/css')

    def page_js(self):
        return self.get('text/javascript')

ext_registry = {
    'txt': 'text/plain',
    'htm': 'text/htm',
    'html': 'text/html',
    'css': 'text/css',
    'js': 'text/javascript'
}
