from os import path
from pysmvt import rg
from pysmvt.application import WSGIApp
from pysmvt.config import DefaultSettings
from pysmvt.middleware import minimal_wsgi_stack
from pysmvt.views import asview
from pysmvt.wrappers import Response

class Settings(DefaultSettings):
    def init(self):
        self.dirs.base = path.dirname(__file__)
        self.appname = path.basename(self.dirs.base)
        DefaultSettings.init(self)

    def get_storage_dir(self):
        return path.join(self.dirs.base, '..', 'test-output', self.appname)

settings = Settings()

app = WSGIApp(settings)
wsgiapp = minimal_wsgi_stack(app)

@asview()
def helloworld():
    return 'Hello World'

@asview('/mms')
def make_me_shorter():
    return 'make_me_shorter'

@asview('/hw/<tome>')
def helloto(tome='World'):
    return 'Hello %s' % tome

@asview('/hw2/<tome>')
def helloto2(nothere=None, tome='World'):
    return 'hw2 %s' % tome

@asview('/flexible/<SEOonly>')
def flexible():
    return 'thats cool'

@asview('/cooler/<SEOonly>', getargs=('foo', 'bar'))
def cooler(SEOonly=None, foo=None, bar=None, willstaynone=None):
    return '%s, %s, %s, %s' % (foo, bar, SEOonly, willstaynone)

@asview('/ap/<foo>', getargs=('foo'))
def argprecedence(foo=None):
    return str(foo)

@asview('/tolist', getargs=('foo'))
def tolist(foo=None):
    return str(foo)

@asview('/wontwork')
def wontwork(foo):
    return 'foo'

@asview('/positional', getargs=('foo'))
def positional(foo):
    return foo

@asview('/positional/<foo>')
def positionalurl(foo):
    return foo

@asview('/positional3/<foo>', getargs=('baz'))
def positionalurl3(foo, baz):
    return foo

@asview()
def cssresponse():
    return Response('body {color:black}', mimetype='text/css')

@asview()
def returnwsgiapp():
    """
        could have just as easily returned Response(), but I wanted to do
        something different!
    """
    def hello_world(environ, start_response):
        start_response('200 OK', [('Content-Type', 'text/html')])
        return ['wsgi hw']
    return hello_world
