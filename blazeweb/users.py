import logging
import random

from blazeutils.datastructures import LazyDict, OrderedDict
from blazeutils.helpers import tolist
from blazeutils.strings import randchars

log = logging.getLogger(__name__)

class User(LazyDict):
    messages_type = OrderedDict

    def __init__(self):
        self.messages = self.messages_type()
        # initialize values
        self.clear()
        LazyDict.__init__(self)

    def _get_is_authenticated(self):
        return self._is_authenticated
    def _set_is_authenticated(self, value):
        self._is_authenticated = value
    is_authenticated = property(_get_is_authenticated, _set_is_authenticated)

    def _get_is_super_user(self):
        return self._is_super_user
    def _set_is_super_user(self, value):
        self._is_super_user = value
    is_super_user = property(_get_is_super_user, _set_is_super_user)

    def clear(self):
        log.debug('SessionUser object getting cleared() of auth info')
        self._is_authenticated = False
        self._is_super_user = False
        self.perms = set()
        LazyDict.clear(self)

    def _has_any(self, haystack, needles, arg_needles):
        needles = set(tolist(needles))
        if len(arg_needles) > 0:
            needles |= set(arg_needles)
        return bool(haystack.intersection(needles))

    def add_perm(self, *perms):
        self.perms |= set(perms)

    def has_perm(self, perm):
        if self.is_super_user:
            return True
        return perm in self.perms

    def has_any_perm(self, perms, *args):
        if self.is_super_user:
            return True
        return self._has_any(self.perms, perms, args)

    def add_message(self, severity, text, ident=None):
        log.debug('SessionUser message added: %s, %s, %s', severity, text, ident)
        # generate random ident making sure random ident doesn't already
        # exist
        if ident is None:
            while True:
                ident = random.randrange(100000, 999999)
                if not self.messages.has_key(ident):
                    break
        self.messages[ident] = UserMessage(severity, text)

    def get_messages(self, clear = True):
        log.debug('SessionUser messages retrieved: %d' % len(self.messages))
        msgs = self.messages.values()
        if clear:
            log.debug('SessionUser messages cleared')
            self.messages = self.messages_type()
        return msgs

    def __repr__(self):
        return '<User (%s): %s, %s, %s>' % (hex(id(self)), self.is_authenticated, self.copy(), self.messages)

class UserMessage(object):

    def __init__(self, severity, text):
        self.severity = severity
        self.text = text

    def __repr__(self):
        return '%s: %s' % (self.severity, self.text)
