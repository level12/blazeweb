from pysmvt.application import request_context as rc
import random

class SessionUser(object):
    
    def __init__(self):
        if 'user' not in rc.session:
            rc.session['user'] = self
            rc.session['user']._is_authenticated = False
            rc.session['user'].attributes = {}
            rc.session['user'].tokens = {}
            rc.session['user'].messages = {}
    
    def set_attr(self, attribute, value):
        rc.session['user'].attributes[attribute] = value
        
    def get_attr(self, attribute, default_value = None):
        try:
            return rc.session['user'].attributes[attribute]
        except KeyError:
            return default_value
    
    def has_attr(self, attribute):
        return rc.session['user'].attributes.has_key(attribute)
    
    def add_perm(self, token):
        rc.session['user'].tokens[token] = True
        
    def has_perm(self, token):
        return rc.session['user'].tokens.has_key(token)

    def add_message(self, severity, text, ident = None):
        # generate random ident making sure random ident doesn't already
        # exist
        if ident is None:
            while True:
                ident = random.randrange(100000, 999999)
                if not rc.session['user'].messages.has_key(ident):
                    break
        rc.session['user'].messages[ident] = UserMessage(severity, text)
    
    def get_messages(self, clear = True):
        msgs = rc.session['user'].messages.values()
        if clear:
            rc.session['user'].messages = {}
        return msgs
    
    def authenticated(self):
        rc.session['user']._is_authenticated = True
        
    def is_authenticated(self):
        return rc.session['user']._is_authenticated

class UserMessage(object):
    
    def __init__(self, severity, text):
        self.severity = severity
        self.text = text