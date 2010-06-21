import logging
import random

from blazeutils.datastructures import LazyDict, OrderedDict
from blazeutils.helpers import tolist
from blazeutils.strings import randchars

from blazeweb import rg

log = logging.getLogger(__name__)

class User(LazyDict):

    def __init__(self):
        self.messages = OrderedDict()
        # initialize values
        self.clear()
        LazyDict.__init__(self)

    def clear(self):
        log.debug('SessionUser object getting cleared() of auth info')
        self.is_authenticated = False
        self.is_super_user = False
        self.tokens = {}
        LazyDict.clear(self)

    def add_token(self, *tokens):
        for token in tokens:
            self.tokens[token] = True

    def has_token(self, token):
        return self.tokens.has_key(token)

    def has_any_token(self, tokens, *args):
        tokens = tolist(tokens)
        if len(args) > 0:
            tokens.extend(args)
        for token in tokens:
            if self.has_token(token):
                return True
        return False

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
            self.messages = {}
        return msgs

    def __repr__(self):
        return '<User (%s): %s, %s, %s>' % (hex(id(self)), self.is_authenticated, self.copy(), self.messages)

class UserMessage(object):

    def __init__(self, severity, text):
        self.severity = severity
        self.text = text

    def __repr__(self):
        return '%s: %s' % (self.severity, self.text)
