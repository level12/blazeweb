import __builtin__
from os import path
import sys

from blazeutils.testing import logging_handler
from nose.tools import eq_

from blazeweb.globals import ag
from blazeweb.hierarchy import hm, findview, HierarchyImportError, findfile, \
    FileNotFound, findobj, listplugins, list_plugin_mappings, visitmods, \
    gatherobjs, findcontent

import config
from newlayout.application import make_wsgi
from blazewebtestapp.applications import make_wsgi as pta_make_wsgi
from minimal2.application import make_wsgi as m2_make_wsgi
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
        eh = logging_handler('blazeweb.hierarchy')
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
        expected = path.join('nlsupporting', 'templates', 'blank.txt')
        assert fullpath.endswith(expected), fullpath

        fullpath = findfile('templates/innl.txt')
        expected = path.join('newlayout', 'templates', 'innl.txt')
        assert fullpath.endswith(expected), fullpath

        try:
            findfile('templates/notthere.txt')
            assert False
        except FileNotFound:
            pass

    def test_plugin_findfile(self):
        fullpath = findfile('news:templates/srcnews.txt')
        expected = path.join('newlayout', 'plugins', 'news', 'templates', 'srcnews.txt')
        assert fullpath.endswith(expected), fullpath

        fullpath = findfile('news:templates/nplug1.txt')
        expected = path.join('newsplug1', 'templates', 'nplug1.txt')
        assert fullpath.endswith(expected), fullpath

        fullpath = findfile('news:templates/nplug2.txt')
        expected = path.join('newsplug2', 'templates', 'nplug2.txt')
        assert fullpath.endswith(expected), fullpath

        fullpath = findfile('news:templates/supporting_news_src.txt')
        expected = path.join('nlsupporting', 'plugins', 'news', 'templates', 'supporting_news_src.txt')
        assert fullpath.endswith(expected), fullpath

        fullpath = findfile('news:templates/nplug3.txt')
        expected = path.join('newsplug3', 'templates', 'nplug3.txt')
        assert fullpath.endswith(expected), fullpath

        try:
            findfile('news:templates/notthere.txt')
            assert False
        except FileNotFound:
            pass

    def test_findfile_cache(self):
        eh = logging_handler('blazeweb.hierarchy')
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

class TestPTA(object):

    @classmethod
    def setup_class(cls):
        pta_make_wsgi('Testruns')

    def test_list_plugins(self):
        expected = ['tests', 'badimport1', 'nomodel', 'nosettings', 'sessiontests', 'routingtests', 'usertests', 'disabled']
        eq_(expected, listplugins())

    def test_gatherobjs(self):
        result = gatherobjs('tasks.init_db', lambda name, obj: name.startswith('action_'))
        eq_(result['appstack.tasks.init_db']['action_000'].__module__, 'blazewebtestapp.tasks.init_db')
        eq_(result['plugstack.routingtests.tasks.init_db']['action_001'].__module__, 'blazewebtestapp.plugins.routingtests.tasks.init_db')
        eq_(result['plugstack.routingtests.tasks.init_db']['action_003'].__module__, 'blazewebtestapp2.plugins.routingtests.tasks.init_db')
        eq_(result['plugstack.tests.tasks.init_db']['action_001'].__module__, 'blazewebtestapp2.plugins.tests.tasks.init_db')
        eq_(result['appstack.tasks.init_db']['action_001'].__module__, 'blazewebtestapp.tasks.init_db')
        eq_(result['appstack.tasks.init_db']['action_002'].__module__, 'blazewebtestapp.tasks.init_db')
        eq_(result['appstack.tasks.init_db']['action_005'].__module__, 'blazewebtestapp2.tasks.init_db')

    def test_find_view_hierarchy_import_errors_get_raised(self):
        try:
            v = findview('badimport1:Index')
            assert False
        except HierarchyImportError, e:
            assert 'module "nothere." not found; searched plugstack' in str(e), e

    def test_find_view_no_plugin(self):
        try:
            v = findview('notaplugin:Foo')
            assert False
        except HierarchyImportError, e:
            assert 'An object for View endpoint "notaplugin:Foo" was not found' == str(e), e

    def test_find_content_no_plugin(self):
        try:
            v = findcontent('notaplugin:Foo')
            assert False
        except HierarchyImportError, e:
            assert 'An object for Content endpoint "notaplugin:Foo" was not found' == str(e), e

    def test_find_content_no_module(self):
        try:
            v = findcontent('routingtests:Foo')
            assert False
        except HierarchyImportError, e:
            assert 'An object for Content endpoint "routingtests:Foo" was not found' == str(e), e

    def test_find_content_no_attribute(self):
        try:
            v = findcontent('tests:NotThere')
            assert False
        except HierarchyImportError, e:
            assert 'An object for Content endpoint "tests:NotThere" was not found' == str(e), e

    def test_find_content_no_object_app_level(self):
        from appstack.content import iexist
        assert iexist
        try:
            v = findcontent('NotThere')
            assert False
        except HierarchyImportError, e:
            assert 'An object for Content endpoint "NotThere" was not found' == str(e), e

    def test_find_content_hierarchy_import_errors_get_raised(self):
        try:
            v = findcontent('badimport1:Foo')
            assert False
        except HierarchyImportError, e:
            assert 'module "nothere." not found; searched plugstack' in str(e), e


class TestMin2(object):
    @classmethod
    def setup_class(cls):
        m2_make_wsgi('Dispatching')

    def test_plugin_mappings(self):
        expected = [('minimal2', 'internalonly', None), ('minimal2', 'news', None), ('minimal2', 'news', 'newsplug4'), ('minimal2', 'foo', 'foobwp')]
        eq_(expected, list_plugin_mappings())

    def test_find_content_no_module_app_level(self):
        try:
            v = findcontent('NotThere')
            assert False
        except HierarchyImportError, e:
            assert 'An object for Content endpoint "NotThere" was not found' == str(e), e

def test_visitmods_reloading():
    m2_make_wsgi()
    rulenum = len(list(ag.route_map.iter_rules()))
    assert rulenum >= 9, ag.route_map

    from minimal2.views import page1
    firstid = id(page1)

    m2_make_wsgi()
    rulenum = len(list(ag.route_map.iter_rules()))
    assert rulenum >= 9, ag.route_map


    from minimal2.views import page1
    secondid = id(page1)

    # we want to make sure that @asview is not creating a new class object
    # each time, but using the cache object that already exists if possible
    eq_(firstid, secondid)
