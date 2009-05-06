import sys
import random
import hashlib
import time
import re
import logging
from pprint import PrettyPrinter
from pysmvt import settings, user, ag, forward, rg, modimport
from werkzeug.debug.tbtools import get_current_traceback
from werkzeug import run_wsgi_app, create_environ
from nose.tools import make_decorator
from formencode.validators import URL
from formencode import Invalid
from markdown2 import markdown

log = logging.getLogger(__name__)

def reindent(s, numspaces):
    """ reinidents a string (s) by the given number of spaces (numspaces) """
    leading_space = numspaces * ' '
    lines = [ leading_space + line.strip()
                for line in s.splitlines()]
    return '\n'.join(lines)

def urlslug(s, length=None):
    import re
    #$slug = str_replace("&", "and", $string);
    # only keep alphanumeric characters, underscores, dashes, and spaces
    s = re.compile( r'[^\/a-zA-Z0-9_ \\-]').sub('', s)
    # replace forward slash, back slash, underscores, and spaces with dashes
    s = re.compile(r'[\/ \\_]+').sub('-', s)
    # make it lowercase
    s = s.lower()
    if length is not None:
        return s[:length-1].rstrip('-')
    else:
        return s

def isurl(s, require_tld=True):
    u = URL(add_http=False, require_tld=require_tld)
    try:
        u.to_python(s)
        return True
    except Invalid:
        url_local = re.compile(r'//localhost(:|/)').search(s)
        if url_local is not None:
            return True
        return False

def tb_depth_in(depths):
    """
    looks at the current traceback to see if the depth of the traceback
    matches any number in the depths list.  If a match is found, returns
    True, else False.
    """
    depths = tolist(depths)
    if traceback_depth() in depths:
        return True
    return False

def traceback_depth(tb=None):
    if tb == None:
        _, _, tb = sys.exc_info()
    depth = 0
    while tb.tb_next is not None:
        depth += 1
        tb = tb.tb_next
    return depth

def fatal_error(user_desc = None, dev_desc = None, orig_exception = None):
    # log stuff
    log.info('Fatal error: "%s" -- %s', dev_desc, str(orig_exception))
    
    # set user message
    if user_desc != None:
        user.add_message('error', user_desc)
        
    # forward to fatal error view
    forward(settings.endpoint.sys_error)

def auth_error(user_desc = None, dev_desc = None):
    # log stuff
    if dev_desc != None:
        log.info('Auth error: %s', dev_desc)
    
    # set user message
    if user_desc != None:
        user.add_message('error', user_desc)
        
    # forward to fatal error view
    forward(settings.endpoint.sys_auth_error)

def bad_request_error(dev_desc = None):
    # log stuff
    if dev_desc != None:
        log.info('bad request error: %s', dev_desc)
        
    # forward to fatal error view
    forward(settings.endpoint.bad_request_error)

# from sqlalchemy
def tolist(x, default=[]):
    if x is None:
        return default
    if not isinstance(x, (list, tuple)):
        return [x]
    else:
        return x
    
def toset(x):
    if x is None:
        return set()
    if not isinstance(x, set):
        return set(tolist(x))
    else:
        return x

def pprint( stuff, indent = 4, asstr=False):
    pp = PrettyPrinter(indent=indent)
    if asstr:
        return pp.pformat(stuff)
    pp.pprint(stuff)

def randchars(n = 12):
    charlist = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    return ''.join(random.choice(charlist) for _ in range(n))

def randhash():
    return hashlib.md5(str(random.random()) + str(time.clock())).hexdigest()

def safe_strftime(value, format='%m/%d/%Y %H:%M', on_none=''):
    if value is None:
        return on_none
    return value.strftime(format)

class OrderedProperties(object):
    """An object that maintains the order in which attributes are set upon it.

    Also provides an iterator and a very basic getitem/setitem
    interface to those attributes.

    (Not really a dict, since it iterates over values, not keys.  Not really
    a list, either, since each value must have a key associated; hence there is
    no append or extend.)
    """

    def __init__(self, initialize=True):
        self._data = OrderedDict()
        self._initialized=initialize
        
    def __len__(self):
        return len(self._data)

    def __iter__(self):
        return self._data.itervalues()

    def __add__(self, other):
        return list(self) + list(other)

    def __setitem__(self, key, object):
        self._data[key] = object

    def __getitem__(self, key):
        return self._data[key]

    def __delitem__(self, key):
        del self._data[key]

    def __setattr__(self, item, value):
        # this test allows attributes to be set in the __init__ method
        if self.__dict__.has_key('_initialized') == False or self.__dict__['_initialized'] == False:
            self.__dict__[item] = value
        # any normal attributes are handled normally when they already exist
        # this would happen if they are given different values after initilization
        elif self.__dict__.has_key(item):       
            self.__dict__[item] = value
        # attributes added after initialization are stored in _data
        else:
            self._set_data_item(item, value)

    def _set_data_item(self, item, value):
        self._data[item] = value

    def __getstate__(self):
        return {'_data': self.__dict__['_data']}

    def __setstate__(self, state):
        self.__dict__['_data'] = state['_data']

    def __getattr__(self, key):
        try:
            return self._data[key]
        except KeyError:
            raise AttributeError(key)

    def __contains__(self, key):
        return key in self._data

    def update(self, value):
        self._data.update(value)

    def get(self, key, default=None):
        if key in self:
            return self[key]
        else:
            return default

    def keys(self):
        return self._data.keys()

    def has_key(self, key):
        return self._data.has_key(key)

    def clear(self):
        self._data.clear()
    
    def todict(self):
        return self._data

class OrderedDict(dict):
    """A dict that returns keys/values/items in the order they were added."""

    def __init__(self, ____sequence=None, **kwargs):
        self._list = []
        if ____sequence is None:
            if kwargs:
                self.update(**kwargs)
        else:
            self.update(____sequence, **kwargs)

    def clear(self):
        self._list = []
        dict.clear(self)

    def sort(self, fn=None):
        self._list.sort(fn)

    def update(self, ____sequence=None, **kwargs):
        if ____sequence is not None:
            if hasattr(____sequence, 'keys'):
                for key in ____sequence.keys():
                    self.__setitem__(key, ____sequence[key])
            else:
                for key, value in ____sequence:
                    self[key] = value
        if kwargs:
            self.update(kwargs)

    def setdefault(self, key, value):
        if key not in self:
            self.__setitem__(key, value)
            return value
        else:
            return self.__getitem__(key)

    def __iter__(self):
        return iter(self._list)

    def values(self):
        return [self[key] for key in self._list]

    def itervalues(self):
        return iter(self.values())

    def keys(self):
        return list(self._list)

    def iterkeys(self):
        return iter(self.keys())

    def items(self):
        return [(key, self[key]) for key in self.keys()]

    def iteritems(self):
        return iter(self.items())

    def __setitem__(self, key, object):
        if key not in self:
            self._list.append(key)
        dict.__setitem__(self, key, object)

    def __delitem__(self, key):
        dict.__delitem__(self, key)
        self._list.remove(key)

    def pop(self, key, *default):
        present = key in self
        value = dict.pop(self, key, *default)
        if present:
            self._list.remove(key)
        return value

    def popitem(self):
        item = dict.popitem(self)
        self._list.remove(item[0])
        return item

class Context(object):
    """
        just a dummy object to hang attributes off of
    """
    pass

def wrapinapp(wsgiapp):
    """Used to make any callable run inside a WSGI application.

    Example use::

        from pysmvt.routing import current_url
        from pysmvt.utils import wrapinapp

        from testproj.applications import make_wsgi
        app = make_wsgi('Test')

        @wrapinapp(app)
        def test_currenturl():
            assert current_url(host_only=True) == 'http://localhost/'
    """
    def decorate(func):
        def newfunc(*arg, **kw):
            def sendtowsgi():
                func(*arg, **kw)
            environ = create_environ('/[[__handle_callable__]]')
            environ['pysmvt.callable'] = sendtowsgi
            run_wsgi_app(wsgiapp, environ)
        newfunc = make_decorator(func)(newfunc)
        return newfunc
    return decorate
