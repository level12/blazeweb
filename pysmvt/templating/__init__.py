from markdown2 import markdown
from pysutils.datetime import safe_strftime
from pysutils.numbers import moneyfmt
from pysutils.strings import simplify_string, reindent

from pysmvt import ag, settings
from pysmvt.content import getcontent
from pysmvt.routing import url_for, current_url
from pysmvt.utils.html import strip_tags

class EngineBase(object):
    """
        This class acts as a bridge between pysmvt and templating engines.
        There are (deliberately) few places where pysmvt objects interact
        with the templating engine.  When that takes places, they do so
        through a translator object.  You are free to interact with your
        templating engine API directly, but when pysmvt objects do it,
        they go through the unified API of an instance of this class.
    """

    def __init__(self):
        raise NotImplementedError('Translor must be subclassed')

    def render_string(string, context):
        raise NotImplementedError('Translor must be subclassed')

    def render_template(string, context):
        raise NotImplementedError('Translor must be subclassed')

    def get_globals(self):
        globals = {}
        globals['url_for'] = url_for
        globals['current_url'] = current_url
        #globals['inc_css'] = self.include_css
        #globals['inc_js'] = self.include_js
        globals['inc_content'] = getcontent
        #globals['response_css'] = self.page_css
        #globals['response_js'] = self.page_js
        return globals

    def get_filters(self):
        filters = {}
        filters['simplify'] = simplify_string
        filters['markdown'] = markdown
        filters['strip_tags'] = strip_tags
        filters['moneyfmt'] = moneyfmt
        filters['datefmt'] = safe_strftime
        return filters

def render_template(endpoint, **context):
    return ag.tplengine.render_template(endpoint, context)

def default_engine():
    tmod = __import__('pysmvt.templating.%s' % settings.templating.default_engine, fromlist=[''])
    tobj = getattr(tmod, 'Translator')
    return tobj
