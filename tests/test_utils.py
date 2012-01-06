from __future__ import with_statement
from os import path

from nose.tools import eq_
from blazeutils.strings import normalizews
from webtest import TestApp

from blazeweb.globals import settings
from blazeweb.utils.filesystem import copy_static_files, mkdirs

import config
from scripting_helpers import script_test_path, env
from newlayout.application import make_wsgi

def assert_contents(text, fpath):
    fpath = path.join(script_test_path, fpath)
    with open(fpath) as f:
        eq_(text, f.read().strip())

class TestFirstApp(object):

    @classmethod
    def setup_class(cls):
        cls.app = make_wsgi()
        cls.ta = TestApp(cls.app)
        env.clear()

    def tearDown(self):
        env.clear()

    def test_copy_static_files(self):
        copy_static_files()

        # app files
        assert_contents('newlayout', path.join('newlayout', 'static', 'app', 'statictest.txt'))
        assert_contents('nlsupporting', path.join('newlayout', 'static', 'app', 'statictest2.txt'))

        # app component files
        assert_contents('newlayout:news', path.join('newlayout', 'static', 'component', 'news', 'statictest.txt'))
        assert_contents('nlsupporting:news', path.join('newlayout', 'static', 'component', 'news', 'statictest4.txt'))

        # external component files
        assert_contents('newscomp1', path.join('newlayout', 'static', 'component', 'news', 'statictest2.txt'))
        assert_contents('newscomp2', path.join('newlayout', 'static', 'component', 'news', 'statictest3.txt'))
        assert_contents('newscomp3', path.join('newlayout', 'static', 'component', 'news', 'statictest5.txt'))

    def test_removal(self):
        # create test files so we know if they are deleted
        mkdirs(path.join(script_test_path, 'newlayout', 'static', 'app'))
        mkdirs(path.join(script_test_path, 'newlayout', 'static', 'component', 'news'))
        app_fpath = path.join(script_test_path, 'newlayout', 'static', 'app', 'inapp.txt')
        component_fpath = path.join(script_test_path, 'newlayout', 'static', 'component', 'news', 'incomponent.txt')
        root_fpath = path.join(script_test_path, 'newlayout', 'static', 'inroot.txt')
        open(app_fpath, 'w')
        open(component_fpath, 'w')
        open(root_fpath, 'w')

        copy_static_files(delete_existing=True)

        # make sure at least one file is there from the static copies
        assert_contents('newlayout', path.join('newlayout', 'static', 'app', 'statictest.txt'))

        # app and component dirs should have been deleted
        assert not path.exists(app_fpath)
        assert not path.exists(component_fpath)

        # other items in the static directory are still there
        assert path.exists(root_fpath)

    def test_static_server(self):
        copy_static_files(delete_existing=True)
        r = self.ta.get('/static/app/statictest.txt')
        assert 'newlayout' in r

class TestAborting(object):

    @classmethod
    def setup_class(cls):
        cls.app = make_wsgi('WithTestSettings')
        cls.ta = TestApp(cls.app)
        env.clear()

    def test_integer(self):
        r = self.ta.get('/abort/int', status=400)
        r.mustcontain('400 Bad Request')

    def test_callable(self):
        r = self.ta.get('/abort/callable')
        assert 'test Response' in r, r

    def test_str(self):
        r = self.ta.get('/abort/str')
        r.mustcontain('test &amp; str')

    def test_other(self):
        r = self.ta.get('/abort/other')
        # linux doesn't escape single quotes, windows does
        assert "'b&amp;z': 1, 'foo': 'bar'}</pre>" in r or "&#39;b&amp;z&#39;: 1, &#39;foo&#39;: &#39;bar&#39;}</pre>" in r, r

    def test_dabort(self):
        r = self.ta.get('/abort/dabort')
        r.mustcontain("<pre>[]</pre>")

def test_auto_copy():
    env.clear()
    app = make_wsgi('AutoCopyStatic')

    # make sure at least one file is there from the static copies
    assert_contents('newlayout', path.join('newlayout', 'static', 'app', 'statictest.txt'))
    env.clear()
