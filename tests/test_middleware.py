import config
import unittest

from nose.tools import eq_
from webtest import TestApp

import config
from newlayout.application import make_wsgi

class TestStaticFileServer(object):

    @classmethod
    def setup_class(cls):
        cls.app = make_wsgi('ForStaticFileTesting')
        cls.ta = TestApp(cls.app)

    def test_no_path_after_type(self):
        self.ta.get('/static/app', status=404)
        self.ta.get('/static/app/', status=404)

    def test_bad_type(self):
        self.ta.get('/static/foo/something.txt', status=404)

    def test_no_component(self):
        self.ta.get('/static/component/', status=404)
        self.ta.get('/static/component', status=404)

    def test_top_level_file(self):
        r = self.ta.get('/static/app/statictest.txt')
        assert 'newlayout' in r, r

    def test_from_supporting_app(self):
        r = self.ta.get('/static/app/statictest2.txt')
        assert 'nlsupporting' in r, r

    def test_from_internal_component(self):
        r = self.ta.get('/static/component/news/statictest.txt')
        assert 'newlayout:news' in r, r

    def test_from_external_component(self):
        r = self.ta.get('/static/component/news/statictest5.txt')
        assert 'newscomp3' in r, r
