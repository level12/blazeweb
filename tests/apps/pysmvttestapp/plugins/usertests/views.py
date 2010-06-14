from pysmvt import session, user
from pysmvt.views import View

class SetFoo(View):

    def default(self):
        existing = user.get_attr('foo')
        if existing:
            raise Exception('user attribute "foo" existed')
        user.set_attr('foo', 'bar')
        user.set_attr('bar', 'baz')
        return 'foo set'

class GetFoo(View):

    def default(self):
        return '%s%s' % (user.get_attr('foo'), user.get_attr('bar'))


class SetAuthenticated(View):

    def default(self):
        user.authenticated()

class GetAuthenticated(View):

    def default(self):
        return str(user.is_authenticated())

class AddPerm(View):

    def default(self):
        user.add_perm('foo-bar')

class GetPerms(View):

    def default(self):
        return '%s%s' % (user.has_perm('foo-bar'), user.has_perm('foo-baz'))

class Clear(View):

    def default(self):
        user.set_attr('foo', 'bar')
        user.add_perm('foo-bar')
        user.authenticated()
        user.clear()
        return '%s%s%s' % (user.is_authenticated(), user.has_perm('foo-bar'), user.get_attr('foo'))

class SetMessage(View):

    def default(self):
        user.add_message('test', 'my message')

class GetMessage(View):

    def default(self):
        return str(user.get_messages()[0])

class GetNoMessage(View):

    def default(self):
        return str(len(user.get_messages()))
