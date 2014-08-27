import unittest

import config
from blazewebtestapp.applications import make_wsgi
from werkzeug import Client, BaseResponse
from blazeweb.testing import TestApp
from nose.tools import eq_
import os
from time import sleep

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


class TestBeakerCleanup(unittest.TestCase):
    def test_session_cleanup(self):
        from minimal2.application import make_wsgi as min_make_wsgi
        from blazeweb.globals import settings

        wsgiapp = min_make_wsgi('BeakerSessions')
        ta = TestApp(wsgiapp)
        ta.get('/hassession')

        for i in range(10):
            open(os.path.join(settings.beaker.data_dir, str(i)), 'a').close()
            if i == 5:
                # files 6, 7, 8, 9 will be within timeout
                sleep(2)

        def count_files():
            return len([
                f for f in os.listdir(settings.beaker.data_dir)
                if os.path.isfile(os.path.join(settings.beaker.data_dir, f))
            ])

        assert count_files() > 5
        wsgiapp = min_make_wsgi('BeakerSessions')
        eq_(count_files(), 4)

        # cleanup
        for i in range(6, 10):
            os.remove(os.path.join(settings.beaker.data_dir, str(i)))
