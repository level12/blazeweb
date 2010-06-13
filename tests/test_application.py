from nose.tools import eq_

from pysmvt import settings, ag

import config
from newlayout.application import make_wsgi

def setup_module():
    app = make_wsgi()

def test_plugin_settings():
    assert settings.plugins.news.foo == 1
    assert settings.plugins.news.bar == 3

    eq_( """Map([[<Rule '/fake/route' -> news:notthere>]]) """.strip(), str(ag.route_map))
