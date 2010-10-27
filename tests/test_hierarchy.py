import __builtin__
from os import path
import sys

from blazeutils.testing import logging_handler
from nose.tools import eq_

from blazeweb.globals import ag
from blazeweb.hierarchy import hm, findview, HierarchyImportError, findfile, \
    FileNotFound, findobj, listcomponents, list_component_mappings, visitmods, \
    gatherobjs, findcontent

import config
from newlayout.application import make_wsgi
from blazewebtestapp.applications import make_wsgi as pta_make_wsgi
from minimal2.application import make_wsgi as m2_make_wsgi
class TestMostStuff(object):

    @classmethod
    def setup_class(cls):
        app = make_wsgi()

    def test_component_view(self):
        view = findview('news:FakeView')
        assert 'newlayout.components.news.views.FakeView' in str(view), view

        from compstack.news.views import FakeView
        assert view is FakeView, (view, FakeView)

    def test_compstack_import_overrides(self):
        import newlayout.components.news.views as nlviews
        import newscomp1.views as np1views
        import nlsupporting.components.news as nlsnews

        from compstack.news.views import FakeView
        assert nlviews.FakeView is FakeView

        # test with "as"
        from compstack.news.views import FakeView as psFakeView
        assert nlviews.FakeView is psFakeView

        # test two attributes from different modules
        from compstack.news.views import FakeView, InNewsComp1
        assert nlviews.FakeView is psFakeView
        assert np1views.InNewsComp1 is InNewsComp1

        # testing import from main module
        from compstack.news import somefunc
        assert nlsnews.somefunc is somefunc

    def test_component_import_failures(self):
        # test non-attribute import
        try:
            import compstack.news.views
            assert False
        except HierarchyImportError, e:
            if 'non-attribute importing is not supported' not in str(e):
                raise

        # test no module found
        try:
            from compstack.something.notthere import foobar
            assert False
        except HierarchyImportError, e:
            assert str(e) == 'module "something.notthere" not found; searched compstack'

        # test module exists, but attribute not found
        try:
            from compstack.news.views import nothere
            assert False
        except HierarchyImportError, e:
            assert str(e) == 'attribute "nothere" not found; searched compstack.news.views'

        # test importing from compstack directly
        try:
            from compstack import news
            assert False
        except ImportError, e:
            if 'No module named compstack' not in str(e):
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

        # test importing from compstack directly
        try:
            from appstack import views
            assert False
        except ImportError, e:
            if 'No module named appstack' not in str(e):
                raise

    def test_package_component(self):
        view = findview('news:InNewsComp1')
        assert 'newscomp1.views.InNewsComp1' in str(view)

    def test_package_component_two_deep(self):
        view = findview('news:InNewsComp2')
        assert 'newscomp2.views.InNewsComp2' in str(view)

    def test_from_supporting_app_internal_component(self):
        view = findview('news:InNlSupporting')
        assert 'nlsupporting.components.news.views.InNlSupporting' in str(view)

    def test_from_supporting_app_external_component(self):
        view = findview('news:InNewsComp3')
        assert 'newscomp3.views.InNewsComp3' in str(view)

    def test_package_component_priority(self):
        # upper external components have priority over lower externals
        view = findview('news:News1HasPriority')
        assert 'newscomp1.views.News1HasPriority' in str(view)

        # components in the application have priority over externals
        view = findview('news:InAppHasPriority')
        assert 'newlayout.components.news.views.InAppHasPriority' in str(view)

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
        assert 'newlayout.components.news.views.FakeView' in str(view), view

    def test_app_level_view(self):
        view = findview('AppLevelView')
        assert 'newlayout.views.AppLevelView' in str(view), view

    def test_disabled_component(self):
        try:
            view = findview('pdisabled:FakeView')
            assert False
        except HierarchyImportError, e:
            assert 'An object for View endpoint "pdisabled:FakeView" was not found' in str(e), e

    def test_no_setting_component(self):
        try:
            view = findview('pnosetting:FakeView')
            assert False
        except HierarchyImportError, e:
            assert 'An object for View endpoint "pnosetting:FakeView" was not found' in str(e)

    def test_good_component_but_object_not_there(self):
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

    def test_component_findfile(self):
        fullpath = findfile('news:templates/srcnews.txt')
        expected = path.join('newlayout', 'components', 'news', 'templates', 'srcnews.txt')
        assert fullpath.endswith(expected), fullpath

        fullpath = findfile('news:templates/ncomp1.txt')
        expected = path.join('newscomp1', 'templates', 'ncomp1.txt')
        assert fullpath.endswith(expected), fullpath

        fullpath = findfile('news:templates/ncomp2.txt')
        expected = path.join('newscomp2', 'templates', 'ncomp2.txt')
        assert fullpath.endswith(expected), fullpath

        fullpath = findfile('news:templates/supporting_news_src.txt')
        expected = path.join('nlsupporting', 'components', 'news', 'templates', 'supporting_news_src.txt')
        assert fullpath.endswith(expected), fullpath

        fullpath = findfile('news:templates/ncomp3.txt')
        expected = path.join('newscomp3', 'templates', 'ncomp3.txt')
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
        assert 'newlayout.components.news.views.FakeView' in str(view), view

        view = findobj('views.AppLevelView')
        assert 'newlayout.views.AppLevelView' in str(view), view

    def test_list_components(self):
        plist = ['news', 'pnoroutes', 'badimport']
        eq_(plist, listcomponents())

        plist.reverse()
        eq_(plist, listcomponents(reverse=True))

    def test_component_mappings(self):
        plist = [('newlayout', 'news', None), ('newlayout', 'news', 'newscomp1'), ('newlayout', 'news', 'newscomp2'), ('newlayout', 'pnoroutes', None), ('newlayout', 'badimport', None), ('nlsupporting', 'news', None), ('nlsupporting', 'news', 'newscomp3')]
        eq_(plist, list_component_mappings())


        plistwapps = [('newlayout',  None, None), ('newlayout', 'news', None), ('newlayout', 'news', 'newscomp1'), ('newlayout', 'news', 'newscomp2'), ('newlayout', 'pnoroutes', None), ('newlayout', 'badimport', None), ('nlsupporting',  None, None), ('nlsupporting', 'news', None), ('nlsupporting', 'news', 'newscomp3')]
        eq_(plistwapps, list_component_mappings(inc_apps=True))

        plist.reverse()
        eq_(plist, list_component_mappings(reverse=True))

        plist = [('newlayout', 'news', None), ('newlayout', 'news', 'newscomp1'), ('newlayout', 'news', 'newscomp2'), ('nlsupporting', 'news', None), ('nlsupporting', 'news', 'newscomp3')]
        eq_(plist, list_component_mappings('news'))

    def test_visitmods(self):
        bset = set(sys.modules.keys())
        visitmods('tovisit')
        aset = set(sys.modules.keys())
        eq_(aset.difference(bset), set(['nlsupporting.tovisit', 'nlsupporting.components.news.tovisit', 'newlayout.components.badimport.tovisit', 'newscomp3.tovisit', 'newlayout.components.news.tovisit', 'newlayout.tovisit']))

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

    def test_list_components(self):
        expected = ['tests', 'badimport1', 'nomodel', 'nosettings', 'sessiontests', 'routingtests', 'usertests', 'disabled']
        eq_(expected, listcomponents())

    def test_gatherobjs(self):
        result = gatherobjs('tasks.init_db', lambda name, obj: name.startswith('action_'))
        eq_(result['appstack.tasks.init_db']['action_000'].__module__, 'blazewebtestapp.tasks.init_db')
        eq_(result['compstack.routingtests.tasks.init_db']['action_001'].__module__, 'blazewebtestapp.components.routingtests.tasks.init_db')
        eq_(result['compstack.routingtests.tasks.init_db']['action_003'].__module__, 'blazewebtestapp2.components.routingtests.tasks.init_db')
        eq_(result['compstack.tests.tasks.init_db']['action_001'].__module__, 'blazewebtestapp2.components.tests.tasks.init_db')
        eq_(result['appstack.tasks.init_db']['action_001'].__module__, 'blazewebtestapp.tasks.init_db')
        eq_(result['appstack.tasks.init_db']['action_002'].__module__, 'blazewebtestapp.tasks.init_db')
        eq_(result['appstack.tasks.init_db']['action_005'].__module__, 'blazewebtestapp2.tasks.init_db')

    def test_find_view_hierarchy_import_errors_get_raised(self):
        try:
            v = findview('badimport1:Index')
            assert False
        except HierarchyImportError, e:
            assert 'module "nothere." not found; searched compstack' in str(e), e

    def test_find_view_no_component(self):
        try:
            v = findview('notacomponent:Foo')
            assert False
        except HierarchyImportError, e:
            assert 'An object for View endpoint "notacomponent:Foo" was not found' == str(e), e

    def test_find_content_no_component(self):
        try:
            v = findcontent('notacomponent:Foo')
            assert False
        except HierarchyImportError, e:
            assert 'An object for Content endpoint "notacomponent:Foo" was not found' == str(e), e

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
            assert 'module "nothere." not found; searched compstack' in str(e), e


class TestMin2(object):
    @classmethod
    def setup_class(cls):
        m2_make_wsgi('Dispatching')

    def test_component_mappings(self):
        expected = [('minimal2', 'internalonly', None), ('minimal2', 'news', None), ('minimal2', 'news', 'newscomp4'), ('minimal2', 'foo', 'foobwp')]
        eq_(expected, list_component_mappings())

    def test_find_content_no_module_app_level(self):
        try:
            v = findcontent('NotThere')
            assert False
        except HierarchyImportError, e:
            assert 'An object for Content endpoint "NotThere" was not found' == str(e), e

def test_visitmods_reloading():
    m2_make_wsgi()
    rulenum = len(list(ag.route_map.iter_rules()))
    # if all the tests are run, and reload doesn't work, then this this will
    # fail b/c other tests have already loaded minimal2/views.py
    assert rulenum >= 9, ag.route_map

    from minimal2.views import page1
    firstid = id(page1)

    # reloading should only work once per application, so running it again
    # for the same app should not cause any further side effects
    visitmods('views')
    rulenum2 = len(list(ag.route_map.iter_rules()))
    assert rulenum == rulenum2, ag.route_map

    m2_make_wsgi()
    rulenum = len(list(ag.route_map.iter_rules()))
    # if only this tests is run, and reload doesn't work, then this this will
    # fail b/c the previous m2_make_wsgi() loaded minimal2/views.py
    assert rulenum >= 9, ag.route_map

    from minimal2.views import page1
    secondid = id(page1)

    # we want to make sure that @asview is not creating a new class object
    # each time, but using the cache object that already exists if possible
    eq_(firstid, secondid)
