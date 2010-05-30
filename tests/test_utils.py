from pysmvt.routing import current_url
from pysmvt.utils import wrapinapp

# create the wsgi application that will be used for testing
from pysmvttestapp.applications import make_wsgi
app = make_wsgi('Testruns')

# call test_currenturl() inside of a working wsgi app.  current_url()
# depends on a correct environment being setup and would not work
# otherwise.
@wrapinapp(app)
def test_currenturl():
    assert current_url(host_only=True) == 'http://localhost/'
    
class TestThis(object):
    """ Works for class methods too """
    @wrapinapp(app)
    def test_currenturl(self):
        assert current_url(host_only=True) == 'http://localhost/'