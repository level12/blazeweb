import random
from pysmvt import session
import logging

log = logging.getLogger(__name__)

class SessionUser(object):
    
    def __init__(self):
        log.debug('SessionUser initialized')
        if 'user' not in session:
            log.debug('SessionUser object did not exist in session, initializing')
            session['user'] = self
            session['user'].messages = {}
            self.clear()

    def clear(self):
        log.debug('SessionUser object getting cleared() of auth info')
        session['user']._is_authenticated = False
        session['user'].attributes = {}
        session['user'].tokens = {}

    def set_attr(self, attribute, value):
        session['user'].attributes[attribute] = value
        
    def get_attr(self, attribute, default_value = None):
        try:
            return session['user'].attributes[attribute]
        except KeyError:
            return default_value
    
    def has_attr(self, attribute):
        return session['user'].attributes.has_key(attribute)
    
    def add_perm(self, token):
        session['user'].tokens[token] = True
        
    def has_perm(self, token):
        return session['user'].tokens.has_key(token)

    def add_message(self, severity, text, ident = None):
        log.debug('SessionUser message added')
        # generate random ident making sure random ident doesn't already
        # exist
        if ident is None:
            while True:
                ident = random.randrange(100000, 999999)
                if not session['user'].messages.has_key(ident):
                    break
        session['user'].messages[ident] = UserMessage(severity, text)
    
    def get_messages(self, clear = True):
        log.debug('SessionUser messages retrieved: %d' % len(session['user'].messages))
        msgs = session['user'].messages.values()
        if clear:
            log.debug('SessionUser messages cleared')
            session['user'].messages = {}
        return msgs
    
    def authenticated(self):
        session['user']._is_authenticated = True
        
    def is_authenticated(self):
        return session['user']._is_authenticated

class UserMessage(object):
    
    def __init__(self, severity, text):
        self.severity = severity
        self.text = text