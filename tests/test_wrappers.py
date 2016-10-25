from StringIO import StringIO

from webtest import TestApp

from blazeutils.jsonh import jsonmod
from blazeweb.globals import rg
from blazeweb.testing import inrequest
from blazeweb.wrappers import Request

import config
from newlayout.application import make_wsgi

def setup_module():
   make_wsgi()

class TestRequest(object):

   def test_confirm_muttable(self):
      req = Request.from_values({
          'foo': 'bar',
          'txtfile': (StringIO('my file contents'), 'test.txt'),
      },
      path='/foo?val1=1&val2=2')
      assert req.path == '/foo'
      assert len(req.args) == 2
      assert req.args['val1'] == u'1'
      assert req.args['val2'] == u'2'
      req.args['new'] = 1

   @inrequest()
   def test_replace_http_args(self):
      req = rg.request
      assert req.path == '/[[@inrequest]]', rg.request.path
      assert len(req.args) == 0
      assert len(req.form) == 0
      assert len(req.files) == 0
      req.replace_http_args(data={
          'foo': 'bar',
          'txtfile': (StringIO('my file contents'), 'test.txt'),
      },
      path='/foo?val1=1&val2=2')
      assert rg.request is req
      assert req.path == '/[[@inrequest]]', rg.request.path
      assert len(req.args) == 2
      assert req.args['val1'] == u'1'
      assert req.args['val2'] == u'2'
      assert len(req.form) == 1
      assert req.form['foo'] == u'bar'
      assert len(req.files) == 1
      assert req.files['txtfile'].filename == 'test.txt'

   def test_from_values_outside_context(self):
      req = Request.from_values({'foo':'bar'})
      assert req.form['foo'] == 'bar'

   @inrequest()
   def test_from_values_inside_context(self):
      """
          creating a request should not affect rg.request by default
      """
      first_req = rg.request
      sec_req = Request.from_values({'foo':'bar'})
      assert rg.request is first_req

   @inrequest()
   def test_from_values_inside_context_with_new_bind(self):
      """
          creating a request can affect rg.request
      """
      first_req = rg.request
      sec_req = Request.from_values({'foo':'bar'}, bind_to_context=True)
      assert rg.request is sec_req

   def test_json_property(self):
      str_data = jsonmod.dumps({'a': 1, 'b': 2})
      req = Request.from_values(str_data, content_type='application/json')
      data = req.json
      assert data['a'] == 1, data

      req = Request.from_values(str_data, content_type='application/vnd.api+json')
      data = req.json
      assert data['a'] == 1, data

      req = Request.from_values(str_data, content_type='application/text')
      data = req.json
      assert data is None, data

   def test_json_property_encoding(self):
      str_data = jsonmod.dumps({'a': u'\u2153'}, ensure_ascii=False).encode('utf8')
      req = Request.from_values(str_data, content_type='applciation/json')
      data = req.json
      assert data['a'] == u'\u2153', data['a']
      assert isinstance(data['a'], unicode)
