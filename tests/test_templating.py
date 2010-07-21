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

   def test_endpoint_template_variable(self):
      try:
         # had to switch the variable name, we are just identifying the problem
         # with this test
         c = getcontent('getcontent.html', __endpoint='foo')
         assert False
      except TypeError, e:
         assert "getcontent() got multiple values for keyword argument '__endpoint'" == str(e)

      c = getcontent('getcontent.html', endpoint='foo')
      assert c.primary == 'the endpoint: foo', c.primary

   def test_nested_content(self):
      c = getcontent('nesting_content.html', endpoint='foo')
      body = c.primary
      assert '/* nesting_content.css */' in body
      assert '// nesting_content.js' in body
      assert 'nesting_content.htmlnesting_content2.html' in body, body
      assert 'nesting_content2.html' in body, body
      assert 'nc2 arg1: foo' in body, body
      assert '/* nesting_content2.css */' in body, body
      assert body.count('nesting_content2.html') == 1, body
      assert 'nesting_content3.html' in body, body
      assert '/* nesting_content3.css */' in body, body

   def test_page_methods_are_not_autoescaped(self):
      c = getcontent('nesting_content.html', endpoint='foo')
      body = c.primary
      # JS
      assert '// no & autoescape' in body, body
      # CSS
      assert '/* no & autoescape */' in body, body

   def test_page_method_formatting(self):
      c = getcontent('nesting_content2.html')
      icss = '        /* nesting_content2.css */\n' +\
             '        \n' + \
             '        /* nesting_content3.css */'
      css = """/* nesting_content2.css */

/* nesting_content3.css */"""
      assert css in c.page_css(reindent=None), c.page_css()
      assert icss in c.page_css(), c.page_css()

      ijs = '        // nesting_content2.js'
      js = '// nesting_content2.js'
      assert js == c.page_js(reindent=None), c.page_js()
      assert ijs == c.page_js(), c.page_js()

   def test_included_content_default_safe(self):
      c = getcontent('nesting_content.html', endpoint='foo')
      body = c.primary
      assert 'nc2 autoescape: &amp; False' in c.primary, c.primary

   def test_direct_includes(self):
      c = getcontent('direct_include.html')
      body = c.primary
      assert 'nesting_content2.html' in body, body
      assert 'nesting_content3.html' in body, body
      assert '/* nesting_content2.css */' in body, body
      assert '// nesting_content2.js' in body
      assert '/* nesting_content3.css */' in body, body

   @inrequest()
   def test_in_request_usage(self):
      user.name = 'foo'
      c = getcontent('user_test.html')
      assert c.primary == 'user\'s name: foo', c.primary

   @inrequest()
   def test_context_variable_takes_precedence(self):
      user.name = 'foo'
      class MyUser(object):
         name = 'bar'
      c = getcontent('user_test.html', user=MyUser())
      assert c.primary == 'user\'s name: bar', c.primary
