from pysmvt.routing import current_url
from pysmvt.utils import wrapinapp
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
    