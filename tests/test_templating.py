from pysmvt.content import getcontent, Content

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
