# -*- coding: utf-8 -*-

from pysmvt import session, user
from pysmvt.view import RespondingViewBase

class SetFoo(RespondingViewBase):
    
    def default(self):
        existing = user.get_attr('foo')
        if existing:
            raise Exception('user attribute "foo" existed')
        user.set_attr('foo', 'bar')
        session['user'].set_attr('bar', 'baz')
        return 'foo set'

class GetFoo(RespondingViewBase):

    def default(self):
        return '%s%s' % (user.get_attr('foo'), user.get_attr('bar'))


class SetAuthenticated(RespondingViewBase):

    def default(self):
        user.authenticated()

class GetAuthenticated(RespondingViewBase):

    def default(self):
        return user.is_authenticated()

class AddPerm(RespondingViewBase):

    def default(self):
        user.add_perm('foo-bar')

class GetPerms(RespondingViewBase):

    def default(self):
        return '%s%s' % (user.has_perm('foo-bar'), user.has_perm('foo-baz'))

class Clear(RespondingViewBase):

    def default(self):
        user.set_attr('foo', 'bar')
        user.add_perm('foo-bar')
        user.authenticated()
        user.clear()
        return '%s%s%s' % (user.is_authenticated(), user.has_perm('foo-bar'), user.get_attr('foo'))

class SetMessage(RespondingViewBase):

    def default(self):
        user.add_message('test', 'my message')

class GetMessage(RespondingViewBase):

    def default(self):
        return user.get_messages()[0]

class GetNoMessage(RespondingViewBase):

    def default(self):
        return len(user.get_messages())