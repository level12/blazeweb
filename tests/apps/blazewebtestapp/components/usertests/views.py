from blazeweb.globals import user
from blazeweb.views import View

class SetFoo(View):

    def default(self):
        existing = getattr(user, 'foo', None)
        if existing:
            raise Exception('user attribute "foo" existed')
        user.foo = 'bar'
        user.bar = 'baz'
        return 'foo set'

class GetFoo(View):

    def default(self):
        return '%s%s' % (user.foo, user.bar)

class SetAuthenticated(View):

    def default(self):
        user.is_authenticated = True

class GetAuthenticated(View):

    def default(self):
        return str(user.is_authenticated)

class AddPerm(View):

    def default(self):
        user.add_perm('foo-bar')

class GetPerms(View):

    def default(self):
        return '%s%s%s' % (user.has_perm('foo-bar'), user.has_perm('foo-baz'), user.has_any_perm('foo-bar', 'foo-baz'))

class Clear(View):

    def default(self):
        user.foo = 'bar'
        user.add_perm('foo-bar')
        user.is_authenticated = True
        user.clear()
        return '%s%s%s' % (user.is_authenticated, user.has_perm('foo-bar'), getattr(user, 'foo', None))

class SetMessage(View):

    def default(self):
        user.add_message('test', 'my message')

class GetMessage(View):

    def default(self):
        return str(user.get_messages()[0])

class GetNoMessage(View):

    def default(self):
        return str(len(user.get_messages()))
