from markdown2 import markdown
from blazeutils.datetime import safe_strftime
from blazeutils.numbers import moneyfmt
from blazeutils.strings import simplify_string, reindent

from blazeweb.globals import ag, settings, user
from blazeweb.routing import url_for, current_url, static_url
from blazeweb.utils import registry_has_object
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
        globals = {}
        globals['url_for'] = url_for
        globals['current_url'] = current_url
        globals['static_url'] = static_url
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
        filters['static'] = static_url
        return filters

    def update_context(self, context):
        context.setdefault('settings', settings._current_obj())
        if registry_has_object(user):
            context.setdefault('user', user._current_obj())
        else:
            context.setdefault('user', None)

def default_engine():
    tmod = __import__('blazeweb.templating.%s' % settings.templating.default_engine, fromlist=[''])
    tobj = getattr(tmod, 'Translator')
    return tobj
