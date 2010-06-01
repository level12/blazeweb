from pysmvt.routing import current_url
from pysmvt.test import inrequest

# call test_currenturl() with a fake request setup.  current_url()
# depends on a correct environment being setup and would not work
# otherwise.
@inrequest
def test_currenturl():
    assert current_url(host_only=True) == 'http://localhost/'
    
class TestThis(object):
    """ Works for class methods too """
    
    @inrequest
    def test_currenturl(self):
        assert current_url(host_only=True) == 'http://localhost/'