from markdown2 import markdown
from blazeutils.datetime import safe_strftime
from blazeutils.numbers import moneyfmt
from blazeutils.strings import simplify_string, reindent

from blazeweb import ag, settings
from blazeweb.routing import url_for, current_url
from blazeweb.utils.html import strip_tags

class EngineBase(object):
    """
        This class acts as a bridge between blazeweb and templating engines.
        There are (deliberately) few places where blazeweb objects interact
        with the templating engine.  When that takes places, they do so
        through a translator object.  You are free to interact with your
        templating engine API directly, but when blazeweb objects do it,
        they go through the unified API of an instance of this class.
    """

    def __init__(self):
        raise NotImplementedError('Translor must be subclassed')

    def render_string(string, context):
        raise NotImplementedError('Translor must be subclassed')

    def render_template(string, context):
        raise NotImplementedError('Translor must be subclassed')

    def get_globals(self):
        # circular import fun!!
        from blazeweb.content import getcontent
        globals = {}
        globals['url_for'] = url_for
        globals['current_url'] = current_url
        #globals['inc_css'] = self.include_css
        #globals['inc_js'] = self.include_js
        globals['getcontent'] = getcontent
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
    tmod = __import__('blazeweb.templating.%s' % settings.templating.default_engine, fromlist=[''])
    tobj = getattr(tmod, 'Translator')
    return tobj
