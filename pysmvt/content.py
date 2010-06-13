from os import path

from pysmvt import ag, settings
from pysmvt.hierarchy import findcontent, findfile

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
        self.data = u''

    def settype(self):
        self.type = 'text/plain'

    def process(self, args, kwargs):
        self.settype()
        self.data = self.create(*args, **kwargs)

    def create(self):
        return u''

    def add_content(self, content, type):
        self.content.setdefault(type, [])
        self.content[type] = content

    def __unicode__(self):
        return self.data

class TemplateContent(Content):

    def __init__(self, endpoint):
        Content.__init__(self)
        self.endpoint = endpoint

    def settype(self):
        _, ext = path.splitext(self.endpoint)
        self.type = ext_registry[ext.lstrip('.')]

    def create(self, **kwargs):
        return render_template(self.endpoint, **kwargs)

ext_registry = {
    'txt': 'text/plain',
    'htm': 'text/htm',
    'html': 'text/html',
    'css': 'text/css',
    'js': 'text/javascript'
}

# circular import fun!!
from pysmvt.templating import render_template
