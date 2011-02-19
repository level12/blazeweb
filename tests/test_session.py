import unittest

import config
from blazewebtestapp.applications import make_wsgi
from werkzeug import Client, BaseResponse
from blazeweb.testing import TestApp

class TestSession(unittest.TestCase):

    def setUp(self):
        self.app = make_wsgi('Testruns')
        #settings.logging.levels.append(('debug', 'info'))
        self.client = Client(self.app, BaseResponse)

    def tearDown(self):
        self.client = None
        self.app = None

    def test_session_persist(self):
        r = self.client.get('/sessiontests/setfoo')

        self.assertEqual(r.status, '200 OK')
        self.assertEqual(r.data, 'foo set')

        r = self.client.get('/sessiontests/getfoo')

        self.assertEqual(r.status, '200 OK')
        self.assertEqual(r.data, 'bar')

    def test_session_regen_id(self):
        ta = TestApp(self.app)

        r = ta.get('/sessiontests/setfoo', status=200)
        assert r.session['foo'] == 'bar'
        sid = r.session.id
        assert sid in r.headers['Set-Cookie']

        r = ta.get('/sessiontests/regenid', status=200)
        assert r.session.id != sid
        assert r.session.id in r.headers['Set-Cookie']

        r = ta.get('/sessiontests/getfoo', status=200)
        assert r.body == 'bar'
