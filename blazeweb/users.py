import logging
import random

from blazeutils.datastructures import LazyDict, OrderedDict
from blazeutils.helpers import tolist
from blazeutils.strings import randchars
from blazeweb.globals import rg, user as guser
from blazeweb.utils import registry_has_object

log = logging.getLogger(__name__)

class User(LazyDict):
    messages_class = OrderedDict

    def __init__(self):
        self._messages = self.messages_class()
        # initialize values
        self.clear()
        LazyDict.__init__(self)

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

    def __nonzero__(self):
        # lazy dict would return False if it was empty, but we want to look more
        # like just an object if tested for a bool value
        return True

class UserMessage(object):

    def __init__(self, severity, text):
        self.severity = severity
        self.text = text

    def __repr__(self):
        return '%s: %s' % (self.severity, self.text)

class UserProxy(object):
    """
        Track usage of the users global object.

        Initially, the global user is set to an instance of UserProxy.
        If UserProxy is accessed, a real User object is created and assigned
        to the user global object.  The UserProxy will then be garbage
        collected and future accesses to the global user object will
        go directly to that object.

        This code adapted from paste.registry.
    """

    user_cls = User

    def _new_user_instance(self):
        return self.user_cls()

    def _user(self):
        """Lazy initial creation of user object"""
        if '_user_inst' in self.__dict__:
            # if we get called a second time, then
            # there is already a User instance behind the "user" SOP, that
            # means something called user._curr_obj() and got ahold of this
            # UserProxy instance.  The problem is, the code is likely going
            # to continue calling this instance, instead of the "user" SOP,
            # therefore, we need to continue proxying the real User instance
            # hoping the calling code lets go of us eventually
            # If we continue, didn't do this the code below would try to pop the
            # User instance off the SOP and throw a TypeError
            return self.__dict__['_user_inst']

        # load user instance from the beaker session if possible
        if registry_has_object(rg) and rg.session is not None:
            if '__blazeweb_user' in rg.session:
                user_inst = rg.session['__blazeweb_user']
            else:
                user_inst = self._new_user_instance()
                rg.session['__blazeweb_user'] = user_inst
        else:
            user_inst = self._new_user_instance()

        # save the user instance in case we get called again
        self.__dict__['_user_inst'] = user_inst

        # replace underlying object on the user global variable to be the real
        # user instance.  The user has been accessed, so no need to proxy
        # anymore.  After we replace ourselves, future calls to the global
        # "user" SOP variable will go to the real user instance, instead of
        # this UserProxy instance.
        if registry_has_object(guser):
            guser_cur_obj = guser._current_obj()
            if not isinstance(guser_cur_obj, UserProxy):
                raise TypeError('UserProxy tried to unregister a class of type: %s' % cobj)
            rg.environ['paste.registry'].register(guser, user_inst)
        return user_inst

    def __getattr__(self, attr):
        return getattr(self._user(), attr)

    def __setattr__(self, attr, value):
        setattr(self._user(), attr, value)

    def __delattr__(self, name):
        delattr(self._user(), name)

    def __getitem__(self, key):
        return self._user()[key]

    def __setitem__(self, key, value):
        self._user()[key] = value

    def __delitem__(self, key):
        del self._user()[key]

    def __call__(self, *args, **kw):
        return self._user()(*args, **kw)

    def __iter__(self):
        return iter(self._user())

    def __len__(self):
        return len(self._user())

    def __contains__(self, key):
        return key in self._user()

    def __nonzero__(self):
        return bool(self._user())
