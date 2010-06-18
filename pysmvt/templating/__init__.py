from markdown2 import markdown
from pysutils.datetime import safe_strftime
from pysutils.numbers import moneyfmt
from pysutils.strings import simplify_string, reindent

from pysmvt import ag, settings, user
from pysmvt.routing import url_for, current_url
from pysmvt.utils import registry_has_object
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
        # circular import fun!!
        from pysmvt.content import getcontent
        globals = {}
        globals['url_for'] = url_for
        globals['current_url'] = current_url
        globals['getcontent'] = getcontent
        return globals

    def mark_safe(self):
        """ when a template has auto-escaping enabled, mark a value as safe """
        raise NotImplementedError('Translor must be subclassed')

    def get_filters(self):
        filters = {}
        filters['simplify'] = lambda x, *args, **kwargs: self.mark_safe(simplify_string(x, *args, **kwargs))
        filters['markdown'] = lambda x, *args, **kwargs: self.mark_safe(markdown(x, *args, **kwargs))
        filters['strip_tags'] = lambda x: self.mark_safe(striptags(x))
        filters['moneyfmt'] = lambda x, *args, **kwargs: self.mark_safe(moneyfmt(x, *args, **kwargs))
        filters['datefmt'] = safe_strftime
        return filters

    def update_context(self, context):
        toadd = {
            'settings': settings._current_obj(),
        }
        if registry_has_object(user):
            toadd['user'] = user._current_obj()
        else:
            toadd['user'] = None
        context.update(toadd)

def render_template(endpoint, **context):
    return ag.tplengine.render_template(endpoint, context)

def default_engine():
    tmod = __import__('pysmvt.templating.%s' % settings.templating.default_engine, fromlist=[''])
    tobj = getattr(tmod, 'Translator')
    return tobj
