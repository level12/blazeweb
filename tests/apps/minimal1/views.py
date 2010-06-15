from blazeweb.views import asview
from blazeweb.wrappers import Response

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
