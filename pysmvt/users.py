import random
from pysmvt import rg
import logging

log = logging.getLogger(__name__)

class User(object):
    
    def __init__(self):
        self.messages = {}
        # initialize values
        self.clear()

    def clear(self):
        log.debug('SessionUser object getting cleared() of auth info')
        self._is_authenticated = False
        self.attributes = {}
        self.tokens = {}

    def set_attr(self, attribute, value):
        self.attributes[attribute] = value
        
    def get_attr(self, attribute, default_value = None):
        try:
            return self.attributes[attribute]
        except KeyError:
            return default_value
    
    def has_attr(self, attribute):
        return self.attributes.has_key(attribute)
    
    def add_perm(self, token):
        self.tokens[token] = True
        
    def has_perm(self, token):
        return self.tokens.has_key(token)

    def add_message(self, severity, text, ident = None):
        log.debug('SessionUser message added')
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
    
    def authenticated(self):
        self._is_authenticated = True
        
    def is_authenticated(self):
        return self._is_authenticated

class UserMessage(object):
    
    def __init__(self, severity, text):
        self.severity = severity
        self.text = text

    def __repr__(self):
        return '%s: %s' % (self.severity, self.text)