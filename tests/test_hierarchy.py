import __builtin__
import sys
from traceback import extract_tb

from nose.tools import eq_

from pysutils.error_handling import traceback_depth, get_current_traceback, display_tb
from pysmvt.hierarchy import hm
from pysmvt.testing import logging_handler

import config
from newlayout.application import make_wsgi

app = make_wsgi()

def test_plugin_view():
    view = hm.find_view('news:FakeView')
    assert 'newlayout.plugins.news.views.FakeView' in str(view)
    
def test_package_plugin():
    view = hm.find_view('news:InNewsPlug1')
    assert 'newsplug1.views.InNewsPlug1' in str(view)
    
def test_package_plugin_two_deep():
    view = hm.find_view('news:InNewsPlug2')
    assert 'newsplug2.views.InNewsPlug2' in str(view)
    
def test_from_supporting_app_internal_plugin():
    view = hm.find_view('news:InNlSupporting')
    assert 'nlsupporting.plugins.news.views.InNlSupporting' in str(view)
    
def test_from_supporting_app_external_plugin():
    view = hm.find_view('news:InNewsPlug3')
    assert 'newsplug3.views.InNewsPlug3' in str(view)
    
def test_package_plugin_priority():
    # upper external plugins have priority over lower externals
    view = hm.find_view('news:News1HasPriority')
    assert 'newsplug1.views.News1HasPriority' in str(view)
    
    # plugins in the application have priority over externals
    view = hm.find_view('news:InAppHasPriority')
    assert 'newlayout.plugins.news.views.InAppHasPriority' in str(view)

def test_cache():
    eh = logging_handler('pysmvt.hierarchy')
    view = hm.find_view('news:OnlyForCache')
    dmesgs = ''.join(eh.messages['debug'])
    assert 'in cache' not in dmesgs , dmesgs
    eh.reset()
    view = hm.find_view('news:OnlyForCache')
    dmesgs = ''.join(eh.messages['debug'])
    assert 'in cache' in dmesgs , dmesgs

def test_app_level_view():
    view = hm.find_view('appstack:AppLevelView')
    assert 'newlayout.views.AppLevelView' in str(view), view
    
def test_disabled_plugin():
    try:
        view = hm.find_view('pdisabled:FakeView')
    except ImportError, e:
        assert 'pdisabled:FakeView' in str(e)

def test_no_setting_plugin():
    try:
        view = hm.find_view('pnosetting:FakeView')
    except ImportError, e:
        assert 'pnosetting:FakeView' in str(e)

def test_good_plugin_but_object_not_there():
    try:
        view = hm.find_view('news:nothere')
    except ImportError, e:
        assert 'news:nothere' in str(e)
        
def test_import_error_in_target_gets_raised():
    try:
        view = hm.find_view('badimport:nothere')
    except ImportError, e:
        assert 'No module named foo' == str(e), e