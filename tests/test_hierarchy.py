import __builtin__
import sys

from nose.tools import eq_

from pysmvt.hierarchy import hm, findview, HierarchyImportError, findfile, \
    FileNotFound, findobj, listplugins, list_plugin_mappings, visitmods, \
    gatherobjs
from pysutils.testing import logging_handler

import config
from newlayout.application import make_wsgi
from pysmvttestapp.applications import make_wsgi as pta_make_wsgi

class TestMostStuff(object):

    @classmethod
    def setup_class(cls):
        app = make_wsgi()

    def test_plugin_view(self):
        view = findview('news:FakeView')
        assert 'newlayout.plugins.news.views.FakeView' in str(view), view

        from plugstack.news.views import FakeView
        assert view is FakeView, (view, FakeView)

    def test_plugstack_import_overrides(self):
        import newlayout.plugins.news.views as nlviews
        import newsplug1.views as np1views
        import nlsupporting.plugins.news as nlsnews

        from plugstack.news.views import FakeView
        assert nlviews.FakeView is FakeView

        # test with "as"
        from plugstack.news.views import FakeView as psFakeView
        assert nlviews.FakeView is psFakeView

        # test two attributes from different modules
        from plugstack.news.views import FakeView, InNewsPlug1
        assert nlviews.FakeView is psFakeView
        assert np1views.InNewsPlug1 is InNewsPlug1

        # testing import from main module
        from plugstack.news import somefunc
        assert nlsnews.somefunc is somefunc

    def test_plugin_import_failures(self):
        # test non-attribute import
        try:
            import plugstack.news.views
            assert False
        except HierarchyImportError, e:
            if 'non-attribute importing is not supported' not in str(e):
                raise

        # test no module found
        try:
            from plugstack.something.notthere import foobar
            assert False
        except HierarchyImportError, e:
            assert str(e) == 'module "something.notthere" not found; searched plugstack'

        # test module exists, but attribute not found
        try:
            from plugstack.news.views import nothere
            assert False
        except HierarchyImportError, e:
            assert str(e) == 'attribute "nothere" not found; searched plugstack.news.views'

        # test importing from plugstack directly
        try:
            from plugstack import news
            assert False
        except ImportError, e:
            if 'No module named plugstack' not in str(e):
                raise

    def test_appstack_import_overrides(self):
        import newlayout.views as nlviews
        import nlsupporting.views as nlsviews

        from appstack.views import AppLevelView, AppLevelView2
        assert nlviews.AppLevelView is AppLevelView
        assert nlsviews.AppLevelView2 is AppLevelView2

    def test_appstack_import_failures(self):
        # test non-attribute import
        try:
            import appstack.views
            assert False
        except HierarchyImportError, e:
            if 'non-attribute importing is not supported' not in str(e):
                raise

        # test no module found
        try:
            from appstack.notthere import foobar
            assert False
        except HierarchyImportError, e:
            if str(e) != 'module "notthere" not found; searched appstack':
                raise

        # test module exists, but attribute not found
        try:
            from appstack.views import notthere
            assert False
        except HierarchyImportError, e:
            assert str(e) == 'attribute "notthere" not found; searched appstack.views'

        # test importing from plugstack directly
        try:
            from appstack import views
            assert False
        except ImportError, e:
            if 'No module named appstack' not in str(e):
                raise

    def test_package_plugin(self):
        view = findview('news:InNewsPlug1')
        assert 'newsplug1.views.InNewsPlug1' in str(view)

    def test_package_plugin_two_deep(self):
        view = findview('news:InNewsPlug2')
        assert 'newsplug2.views.InNewsPlug2' in str(view)

    def test_from_supporting_app_internal_plugin(self):
        view = findview('news:InNlSupporting')
        assert 'nlsupporting.plugins.news.views.InNlSupporting' in str(view)

    def test_from_supporting_app_external_plugin(self):
        view = findview('news:InNewsPlug3')
        assert 'newsplug3.views.InNewsPlug3' in str(view)

    def test_package_plugin_priority(self):
        # upper external plugins have priority over lower externals
        view = findview('news:News1HasPriority')
        assert 'newsplug1.views.News1HasPriority' in str(view)

        # plugins in the application have priority over externals
        view = findview('news:InAppHasPriority')
        assert 'newlayout.plugins.news.views.InAppHasPriority' in str(view)

    def test_import_cache(self):
        eh = logging_handler('pysmvt.hierarchy')
        view1 = findview('news:OnlyForCache')
        dmesgs = ''.join(eh.messages['debug'])
        assert 'in cache' not in dmesgs , dmesgs
        eh.reset()
        view2 = findview('news:OnlyForCache')
        dmesgs = ''.join(eh.messages['debug'])
        assert 'in cache' in dmesgs , dmesgs

        assert view1 is view2, (view1, view2)

    def test_cache_namespaces(self):
        # this is contrived example, I know
        from appstack.news.views import FakeView
        assert 'newlayout.news.views.FakeView' in str(FakeView), FakeView

        view = findview('news:FakeView')
        assert 'newlayout.plugins.news.views.FakeView' in str(view), view

    def test_app_level_view(self):
        view = findview('AppLevelView')
        assert 'newlayout.views.AppLevelView' in str(view), view

    def test_disabled_plugin(self):
        try:
            view = findview('pdisabled:FakeView')
            assert False
        except HierarchyImportError, e:
            assert 'An object for View endpoint "pdisabled:FakeView" was not found' in str(e), e

    def test_no_setting_plugin(self):
        try:
            view = findview('pnosetting:FakeView')
            assert False
        except HierarchyImportError, e:
            assert 'An object for View endpoint "pnosetting:FakeView" was not found' in str(e)

    def test_good_plugin_but_object_not_there(self):
        try:
            view = findview('news:nothere')
            assert False
        except HierarchyImportError, e:
            assert 'An object for View endpoint "news:nothere" was not found' in str(e), e

    def test_import_error_in_target_gets_raised(self):
        try:
            view = findview('badimport:nothere')
            assert False
        except ImportError, e:
            assert 'No module named foo' == str(e), e

    def test_app_findfile(self):
        fullpath = findfile('templates/blank.txt')
        assert fullpath.endswith('nlsupporting/templates/blank.txt'), fullpath

        fullpath = findfile('templates/innl.txt')
        assert fullpath.endswith('newlayout/templates/innl.txt'), fullpath

        try:
            findfile('templates/notthere.txt')
            assert False
        except FileNotFound:
            pass

    def test_plugin_findfile(self):
        fullpath = findfile('news:templates/srcnews.txt')
        assert fullpath.endswith('newlayout/plugins/news/templates/srcnews.txt'), fullpath

        fullpath = findfile('news:templates/nplug1.txt')
        assert fullpath.endswith('newsplug1/templates/nplug1.txt'), fullpath

        fullpath = findfile('news:templates/nplug2.txt')
        assert fullpath.endswith('newsplug2/templates/nplug2.txt'), fullpath

        fullpath = findfile('news:templates/supporting_news_src.txt')
        assert fullpath.endswith('nlsupporting/plugins/news/templates/supporting_news_src.txt'), fullpath

        fullpath = findfile('news:templates/nplug3.txt')
        assert fullpath.endswith('newsplug3/templates/nplug3.txt'), fullpath

        try:
            findfile('news:templates/notthere.txt')
            assert False
        except FileNotFound:
            pass

    def test_findfile_cache(self):
        eh = logging_handler('pysmvt.hierarchy')
        fullpath = findfile('templates/forcache.txt')
        dmesgs = ''.join(eh.messages['debug'])
        assert 'in cache' not in dmesgs , dmesgs
        eh.reset()
        fullpath = findfile('templates/forcache.txt')
        dmesgs = ''.join(eh.messages['debug'])
        assert 'in cache' in dmesgs , dmesgs
        eh.reset()

    def test_findobj(self):
        view = findobj('news:views.FakeView')
        assert 'newlayout.plugins.news.views.FakeView' in str(view), view

        view = findobj('views.AppLevelView')
        assert 'newlayout.views.AppLevelView' in str(view), view

    def test_list_plugins(self):
        plist = ['news', 'pnoroutes', 'badimport']
        eq_(plist, listplugins())

        plist.reverse()
        eq_(plist, listplugins(reverse=True))

    def test_plugin_mappings(self):
        plist = [('newlayout', 'news', None), ('newlayout', 'news', 'newsplug1'), ('newlayout', 'news', 'newsplug2'), ('newlayout', 'pnoroutes', None), ('newlayout', 'badimport', None), ('nlsupporting', 'news', None), ('nlsupporting', 'news', 'newsplug3')]
        eq_(plist, list_plugin_mappings())


        plistwapps = [('newlayout',  None, None), ('newlayout', 'news', None), ('newlayout', 'news', 'newsplug1'), ('newlayout', 'news', 'newsplug2'), ('newlayout', 'pnoroutes', None), ('newlayout', 'badimport', None), ('nlsupporting',  None, None), ('nlsupporting', 'news', None), ('nlsupporting', 'news', 'newsplug3')]
        eq_(plistwapps, list_plugin_mappings(inc_apps=True))

        plist.reverse()
        eq_(plist, list_plugin_mappings(reverse=True))

        plist = [('newlayout', 'news', None), ('newlayout', 'news', 'newsplug1'), ('newlayout', 'news', 'newsplug2'), ('nlsupporting', 'news', None), ('nlsupporting', 'news', 'newsplug3')]
        eq_(plist, list_plugin_mappings('news'))

    def test_visitmods(self):
        bset = set(sys.modules.keys())
        visitmods('tovisit')
        aset = set(sys.modules.keys())
        eq_(aset.difference(bset), set(['nlsupporting.tovisit', 'nlsupporting.plugins.news.tovisit', 'newlayout.plugins.badimport.tovisit', 'newsplug3.tovisit', 'newlayout.plugins.news.tovisit', 'newlayout.tovisit']))

        # test that we don't catch another import error
        try:
            visitmods('views')
            assert False
        except ImportError, e:
            if str(e) != 'No module named foo':
                raise

class TestGatherObjs(object):

    @classmethod
    def setup_class(cls):
        pta_make_wsgi('Testruns')

    def test_gatherobjs(self):
        result = gatherobjs('tasks.init_db', lambda name, obj: name.startswith('action_'))
        eq_(result['appstack.tasks.init_db']['action_000'].__module__, 'pysmvttestapp.tasks.init_db')
        eq_(result['plugstack.routingtests.tasks.init_db']['action_001'].__module__, 'pysmvttestapp.plugins.routingtests.tasks.init_db')
        eq_(result['plugstack.routingtests.tasks.init_db']['action_003'].__module__, 'pysmvttestapp2.plugins.routingtests.tasks.init_db')
        eq_(result['plugstack.tests.tasks.init_db']['action_001'].__module__, 'pysmvttestapp2.plugins.tests.tasks.init_db')
        eq_(result['appstack.tasks.init_db']['action_001'].__module__, 'pysmvttestapp.tasks.init_db')
        eq_(result['appstack.tasks.init_db']['action_002'].__module__, 'pysmvttestapp.tasks.init_db')
        eq_(result['appstack.tasks.init_db']['action_005'].__module__, 'pysmvttestapp2.tasks.init_db')
