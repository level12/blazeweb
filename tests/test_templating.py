from blazeutils.testing import raises
from jinja2 import TemplateNotFound
from nose.tools import eq_

from blazeweb.content import getcontent, Content
from blazeweb.globals import user, ag
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

    def test_script_and_link_tags(self):
       c = getcontent('nesting_content.html', endpoint='foo')
       body = c.primary
       assert '<link href="/static/linked_nesting_content.css" rel="stylesheet" type="text/css" />' in body, body
       assert '<script src="/static/linked_nesting_content.js" type="text/javascript"></script>' in body, body
       assert '<link href="static/linked_nesting_content_rel.css" rel="stylesheet" type="text/css" />' in body, body
       assert '<script src="static/linked_nesting_content_rel.js" type="text/javascript"></script>' in body, body
       assert '<link charset="utf-8" href="/static/linked_nesting_content3.css" media="print" rel="stylesheet" type="text/css" />' in body, body
       assert '<script src="/static/linked_nesting_content3.js" type="text/javascript"></script>' in body, body
       # make sure the template functions are returning empty strings and not
       # None
       assert 'None' not in body, body

    def test_css_and_js_urls(self):
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

    def test_include_rst(self):
        c = getcontent('include_rst.html')
        eq_(
            c.primary,
"""
<p>from <em>include_rst.rst</em></p>
<p>from <em>include_rst.rst</em></p>
""".lstrip()
        )

    @raises(TemplateNotFound, 'include_mkdn_nf.mkdn')
    def test_include_markdown_not_found(self):
        c = getcontent('include_mkdn_nf.html')

    def test_include_markdown(self):
        c = getcontent('include_mkdn.html')
        eq_(
            c.primary,
"""
<p>from <em>include_mkdn.mkdn</em></p>
<p>from <em>include_mkdn.mkdn</em></p>
""".lstrip()
        )

    def test_super(self):
        """
            test_super

            had a problem with the way we wrapped block rendering functions
            which resulted in super() not working
        """
        c = getcontent('test_super.html')
        eq_(c.primary.strip(), 'The Title |')

    def test_page_methods_are_not_autoescaped(self):
        c = getcontent('nesting_content.html', endpoint='foo')
        body = c.primary
        # JS
        assert '// no & autoescape' in body, body
        # CSS
        assert '/* no & autoescape */' in body, body

    def test_page_method_formatting(self):
        c = getcontent('nesting_content2.html')
        icss = '/* nesting_content2.css */\n' +\
               '        \n' + \
               '        /* nesting_content3.css */'
        css = '/* nesting_content2.css */\n\n/* nesting_content3.css */'

        ijs = '// nesting_content2.js\n' +\
              '        \n' + \
              '        // nesting_content3.js'
        js = '// nesting_content2.js\n\n// nesting_content3.js'

        # re-indent levels are set through the placeholder method
        c.page_css_ph()
        c.page_js_ph()

        assert icss == c.css_ph.content(), c.css_ph.content()
        assert ijs == c.js_ph.content(), repr(c.js_ph.content())

        # re-indent levels are set through the placeholder method
        c.page_css_ph(reindent=None)
        c.page_js_ph(reindent=None)

        assert css == c.css_ph.content()
        assert js == c.js_ph.content(), repr(c.js_ph.content())

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

    def test_content_filter(self):
        def get_nesting_content2():
            return getcontent('nesting_content2.html')
        c = getcontent('content_filter.html', get_nesting_content2=get_nesting_content2)
        body = c.primary
        assert 'content filter' in body, body
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

    @inrequest()
    def test_user_proxy_in_template(self):
        c = getcontent('user_proxy_test.html')
        # user is not authenticated, so we should see False twice
        assert 'False\nFalse' in c.primary

    def test_string_render(self):
        input = 'Hi {{name}}'
        res = ag.tplengine.render_string(input, {'name': 'bob'})
        eq_(res, 'Hi bob')

    def test_abs_static_url(self):
        # static_url will leave it relative
        input = '{{ static_url("app/c/style.css") }}'
        res = ag.tplengine.render_string(input, {})
        eq_(res, 'static/app/c/style.css')

        # pstatic_url will prefix the relative URL
        input = '{{ abs_static_url("app/c/style.css") }}'
        res = ag.tplengine.render_string(input, {})
        eq_(res, '/static/app/c/style.css')

    def test_render_json(self):
        input = 'var foo = {{ obj | json }};'
        res = ag.tplengine.render_string(input, {'obj': {'some_key': 'This is json formatted'}})
        eq_(res, 'var foo = {"some_key": "This is json formatted"};')
