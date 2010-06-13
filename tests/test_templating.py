from pysmvt.content import getcontent, Content

# create the wsgi application that will be used for testing
import config
from newlayout.application import make_wsgi

def setup_module():
   make_wsgi()

class TestContent(object):

   def test_class_usage(self):
      c = getcontent('HelloWorld')
      print c
   #def test_template_usage(self):
   #   c = getcontent('hello_world.html')
