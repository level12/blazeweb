import logging
import random

from blazeutils.datastructures import LazyDict, OrderedDict
from blazeutils.helpers import tolist
from blazeutils.strings import randchars

log = logging.getLogger(__name__)

class User(LazyDict):
    messages_class = OrderedDict

    def __init__(self):
        self._messages = self.messages_class()
        # initialize values
        self.clear()

        # set this here, before LazyDict.__init__() so that it is an attribute
        # of this class and not put in the LazyDict dictionary
        self._is_modified = False

        LazyDict.__init__(self)

        # now reset ._is_modified b/c some attributes were set in LazyDict
        # init which means _is_modified = True right now, which is not what we
        # want
        self._is_modified = False

    @property
    def is_authenticated(self):
        return self._is_authenticated

    @is_authenticated.setter
    def is_authenticated(self, value):
        self._is_authenticated = value

    @property
    def is_super_user(self):
        return self._is_super_user

    @is_super_user.setter
    def is_super_user(self, value):
        self._is_super_user = value

    def is_modified(self):
        return self._is_modified

    def reset_modified(self):
        self._is_modified = False

    def __setattr__(self, item, value):
        """ make sure we track modified when attributes are set """
        # have to use this notation or we will get a recursion loop
        self.__dict__['_is_modified'] = True
        LazyDict.__setattr__(self, item, value)

    def __setitem__(self, key, value):
        """ make sure we track modified when dict items are set """
        self._is_modified = True
        LazyDict.__setitem__(self, key, value)

    def __delitem__(self, key):
        """ make sure we track modified when dict items are deleted """
        self._is_modified = True
        LazyDict.__delitem__(self, key)

    def clear(self):
        log.debug('SessionUser object getting cleared() of auth info')
        self._is_authenticated = False
        self._is_super_user = False
        self._is_modified = True
        self._perms = set()
        LazyDict.clear(self)

    def _has_any(self, haystack, needles, arg_needles):
        needles = set(tolist(needles))
        if len(arg_needles) > 0:
            needles |= set(arg_needles)
        return bool(haystack.intersection(needles))

    def add_perm(self, *perms):
        self._perms |= set(perms)

    def has_perm(self, perm):
        if self.is_super_user:
            return True
        return perm in self._perms

    def has_any_perm(self, perms, *args):
        if self.is_super_user:
            return True
        return self._has_any(self._perms, perms, args)

    def add_message(self, severity, text, ident=None):
        self._is_modified = True
        log.debug('SessionUser message added: %s, %s, %s', severity, text, ident)
        # generate random ident making sure random ident doesn't already
        # exist
        if ident is None:
            while True:
                ident = random.randrange(100000, 999999)
                if not self._messages.has_key(ident):
                    break
        self._messages[ident] = UserMessage(severity, text)

    def get_messages(self, clear = True):
        log.debug('SessionUser messages retrieved: %d' % len(self._messages))
        msgs = self._messages.values()
        if clear:
            log.debug('SessionUser messages cleared')
            self._messages = self.messages_class()
        return msgs

    def __repr__(self):
        return '<User (%s): %s, %s, %s>' % (hex(id(self)), self.is_authenticated, self.copy(), self._messages)

class UserMessage(object):

    def __init__(self, severity, text):
        self.severity = severity
        self.text = text

    def __repr__(self):
        return '%s: %s' % (self.severity, self.text)
