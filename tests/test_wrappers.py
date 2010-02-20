from StringIO import StringIO
from pysmvt.wrappers import Request
from pysmvt.test import create_request

class TestRequest(object):

    def test_confirm_muttable(self):
        req = create_request({
            'foo': 'bar',
            'txtfile': (StringIO('my file contents'), 'test.txt'),
        },
        path='/foo?val1=1&val2=2')
        assert req.path == '/foo'
        assert len(req.args) == 2
        assert req.args['val1'] == u'1'
        assert req.args['val2'] == u'2'
        req.args['new'] = 1