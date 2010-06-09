from os import path

from nose.tools import eq_

from pysmvt.utils.filesystem import copy_static_files, mkdirs

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
        app = make_wsgi()
        env.clear()

    def tearDown(self):
        env.clear()

    def test_copy_static_files(self):
        copy_static_files()

        # app files
        assert_contents('newlayout', path.join('newlayout', 'static', 'app', 'statictest.txt'))
        assert_contents('nlsupporting', path.join('newlayout', 'static', 'app', 'statictest2.txt'))

        # app plugin files
        assert_contents('newlayout:news', path.join('newlayout', 'static', 'plugins', 'news', 'statictest.txt'))
        assert_contents('nlsupporting:news', path.join('newlayout', 'static', 'plugins', 'news', 'statictest4.txt'))

        # external plugin files
        assert_contents('newsplug1', path.join('newlayout', 'static', 'plugins', 'news', 'statictest2.txt'))
        assert_contents('newsplug2', path.join('newlayout', 'static', 'plugins', 'news', 'statictest3.txt'))
        assert_contents('newsplug3', path.join('newlayout', 'static', 'plugins', 'news', 'statictest5.txt'))

    def test_removal(self):
        # create test files so we know if they are deleted
        mkdirs(path.join(script_test_path, 'newlayout', 'static', 'app'))
        mkdirs(path.join(script_test_path, 'newlayout', 'static', 'plugins', 'news'))
        app_fpath = path.join(script_test_path, 'newlayout', 'static', 'app', 'inapp.txt')
        plugin_fpath = path.join(script_test_path, 'newlayout', 'static', 'plugins', 'news', 'inplugin.txt')
        root_fpath = path.join(script_test_path, 'newlayout', 'static', 'inroot.txt')
        open(app_fpath, 'w')
        open(plugin_fpath, 'w')
        open(root_fpath, 'w')

        copy_static_files(delete_existing=True)

        # make sure at least one file is there from the static copies
        assert_contents('newlayout', path.join('newlayout', 'static', 'app', 'statictest.txt'))

        # app and plugin dirs should have been deleted
        assert not path.exists(app_fpath)
        assert not path.exists(plugin_fpath)

        # other items in the static directory are still there
        assert path.exists(root_fpath)

def test_auto_copy():
    env.clear()
    app = make_wsgi('AutoCopyStatic')

    # make sure at least one file is there from the static copies
    assert_contents('newlayout', path.join('newlayout', 'static', 'app', 'statictest.txt'))
    env.clear()
