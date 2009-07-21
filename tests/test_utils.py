from pysmvt.routing import current_url
from pysmvt.utils import wrapinapp, OrderedProperties
from pysmvt import getview

# create the wsgi application that will be used for testing
from pysmvttestapp.applications import make_wsgi
app = make_wsgi('Testruns')

# call test_currenturl() inside of a working wsgi app.  current_url()
# depends on a correct environment being setup and would not work
# otherwise.
@wrapinapp(app)
def test_currenturl():
    assert current_url(host_only=True) == 'http://localhost/'
    
class TestWrapInApp(object):
    
    @wrapinapp(app)
    def test_currenturl(self):
        """ Works for class methods too """
        assert current_url(host_only=True) == 'http://localhost/'
    
    @wrapinapp(app)
    def test_getview(self):
        assert getview('tests:HwSnippet') == 'Hello World!'    
    
    @wrapinapp(app)
    def test_getview_with_css(self):
        assert getview('tests:HtmlSnippetWithCss') == 'no css'

def test_ordered_properties():
    class Opt(OrderedProperties):
        def __init__(self):
            self.from_init = 1
            OrderedProperties.__init__(self)
    
    o = Opt()
    o.after_init = 2
    
    assert o.from_init == 1
    assert o.__dict__['from_init'] == 1
    assert o.after_init == 2
    assert o._data['after_init'] == 2
    
    del o.from_init
    del o.after_init
    
    assert not hasattr(o, 'from_init')
    assert not hasattr(o, 'after_init')
    
    try:
        del o.not_there
        assert False, 'expected attribute error'
    except AttributeError:
        pass