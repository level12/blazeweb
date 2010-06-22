from blazeweb.content import getcontent, Content
from blazeweb.globals import user
from blazeweb.testing import inrequest

# create the wsgi application that will be used for testing
import config
from newlayout.application import make_wsgi

def setup_module():
   make_wsgi()

class TestContent(object):

   def test_class_usage(self):
      c = getcontent('HelloWorld')
      assert c.primary == 'hello world', c.primary

   def test_template_usage(self):
      c = getcontent('index.html', a='foo')
      assert c.primary == 'app index: foo', c.primary

   @inrequest()
   def test_in_request_usage(self):
      user.name = 'foo'
      c = getcontent('user_test.html')
      assert c.primary == 'user\'s name: foo', c.primary
