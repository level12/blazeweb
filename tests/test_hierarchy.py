import __builtin__
import sys
from traceback import extract_tb

from nose.tools import eq_

from pysmvt.hierarchy import hm, findview, HierarchyImportError, findfile, \
    FileNotFound, findobj
from pysutils.testing import logging_handler

import config
from newlayout.application import make_wsgi

app = make_wsgi()

def test_plugin_view():
    view = findview('news:FakeView')
    assert 'newlayout.plugins.news.views.FakeView' in str(view), view

    from plugstack.news.views import FakeView
    assert view is FakeView, (view, FakeView)

def test_plugstack_import_overrides():
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

def test_plugin_import_failures():
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

def test_appstack_import_overrides():
    import newlayout.views as nlviews
    import nlsupporting.views as nlsviews

    from appstack.views import AppLevelView, AppLevelView2
    assert nlviews.AppLevelView is AppLevelView
    assert nlsviews.AppLevelView2 is AppLevelView2

def test_appstack_import_failures():
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

def test_package_plugin():
    view = findview('news:InNewsPlug1')
    assert 'newsplug1.views.InNewsPlug1' in str(view)

def test_package_plugin_two_deep():
    view = findview('news:InNewsPlug2')
    assert 'newsplug2.views.InNewsPlug2' in str(view)

def test_from_supporting_app_internal_plugin():
    view = findview('news:InNlSupporting')
    assert 'nlsupporting.plugins.news.views.InNlSupporting' in str(view)

def test_from_supporting_app_external_plugin():
    view = findview('news:InNewsPlug3')
    assert 'newsplug3.views.InNewsPlug3' in str(view)

def test_package_plugin_priority():
    # upper external plugins have priority over lower externals
    view = findview('news:News1HasPriority')
    assert 'newsplug1.views.News1HasPriority' in str(view)

    # plugins in the application have priority over externals
    view = findview('news:InAppHasPriority')
    assert 'newlayout.plugins.news.views.InAppHasPriority' in str(view)

def test_import_cache():
    eh = logging_handler('pysmvt.hierarchy')
    view1 = findview('news:OnlyForCache')
    dmesgs = ''.join(eh.messages['debug'])
    assert 'in cache' not in dmesgs , dmesgs
    eh.reset()
    view2 = findview('news:OnlyForCache')
    dmesgs = ''.join(eh.messages['debug'])
    assert 'in cache' in dmesgs , dmesgs

    assert view1 is view2, (view1, view2)

def test_app_level_view():
    view = findview('AppLevelView')
    assert 'newlayout.views.AppLevelView' in str(view), view

def test_disabled_plugin():
    try:
        view = findview('pdisabled:FakeView')
        assert False
    except HierarchyImportError, e:
        assert 'module "pdisabled.views" not found; searched plugstack' in str(e)

def test_no_setting_plugin():
    try:
        view = findview('pnosetting:FakeView')
        assert False
    except HierarchyImportError, e:
        assert 'module "pnosetting.views" not found' in str(e)

def test_good_plugin_but_object_not_there():
    try:
        view = findview('news:nothere')
        assert False
    except HierarchyImportError, e:
        assert 'attribute "nothere" not found; searched plugstack.news.views' in str(e)

def test_import_error_in_target_gets_raised():
    try:
        view = findview('badimport:nothere')
        assert False
    except ImportError, e:
        assert 'No module named foo' == str(e), e

def test_app_findfile():
    fullpath = findfile('templates/blank.txt')
    assert fullpath.endswith('nlsupporting/templates/blank.txt'), fullpath

    fullpath = findfile('templates/innl.txt')
    assert fullpath.endswith('newlayout/templates/innl.txt'), fullpath

    try:
        findfile('templates/notthere.txt')
        assert False
    except FileNotFound:
        pass

def test_plugin_findfile():
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

def test_findfile_cache():
    eh = logging_handler('pysmvt.hierarchy')
    fullpath = findfile('templates/forcache.txt')
    dmesgs = ''.join(eh.messages['debug'])
    assert 'in cache' not in dmesgs , dmesgs
    eh.reset()
    fullpath = findfile('templates/forcache.txt')
    dmesgs = ''.join(eh.messages['debug'])
    assert 'in cache' in dmesgs , dmesgs
    eh.reset()

def test_findobj():
    view = findobj('news:views', 'FakeView')
    assert 'newlayout.plugins.news.views.FakeView' in str(view), view

    view = findobj('views', 'AppLevelView')
    assert 'newlayout.views.AppLevelView' in str(view), view
