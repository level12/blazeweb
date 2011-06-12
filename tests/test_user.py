import unittest

from werkzeug import Client, BaseResponse

from blazeweb.users import User, UserProxy

import config
from blazewebtestapp.applications import make_wsgi


class TestUserFunctional(unittest.TestCase):

    def setUp(self):
        self.app = make_wsgi('Testruns')
        #settings.logging.levels.append(('debug', 'info'))
        self.client = Client(self.app, BaseResponse)

    def tearDown(self):
        self.client = None
        self.app = None

    def test_attr(self):
        r = self.client.get('/usertests/setfoo')

        self.assertEqual(r.status, '200 OK')
        self.assertEqual(r.data, 'foo set')

        r = self.client.get('/usertests/getfoo')

        self.assertEqual(r.status, '200 OK')
        self.assertEqual(r.data, 'barbaz')

    def test_auth(self):
        r = self.client.get('/usertests/setauth')

        self.assertEqual(r.status, '200 OK')

        r = self.client.get('/usertests/getauth')

        self.assertEqual(r.status, '200 OK')
        self.assertEqual(r.data, 'True')

    def test_perm(self):
        r = self.client.get('/usertests/addperm')

        self.assertEqual(r.status, '200 OK')

        r = self.client.get('/usertests/getperms')

        self.assertEqual(r.status, '200 OK')
        self.assertEqual(r.data, 'TrueFalseTrue')

    def test_clear(self):
        r = self.client.get('/usertests/clear')

        self.assertEqual(r.status, '200 OK')
        self.assertEqual(r.data, 'FalseFalseNone')

    def test_message(self):
        r = self.client.get('/usertests/setmsg')

        self.assertEqual(r.status, '200 OK')

        r = self.client.get('/usertests/getmsg')

        self.assertEqual(r.status, '200 OK')
        self.assertEqual(r.data, 'test: my message')

        r = self.client.get('/usertests/nomsg')

        self.assertEqual(r.status, '200 OK')
        self.assertEqual(r.data, '0')

class TestUserUnit(object):
    def _check_empty(self, u):
        assert u.is_authenticated == False
        assert u.is_super_user == False
        assert not u.perms

    def test_defaults(self):
        u = User()
        self._check_empty(u)

    def test_clear(self):
        u = User()
        u.is_authenticated = True
        u.is_super_user = True
        u.add_perm('foobar')
        u.clear()
        self._check_empty(u)

    def test_lazy_dict_attrs(self):
        u = User()
        u.foobar = 1
        assert u['foobar'] == 1

    def test_api_attrs_not_in_dict(self):
        u = User()
        u.foobar = 1

        assert u._is_authenticated == False
        assert not u.has_key('_is_authenticated')

        assert u._is_super_user == False
        assert not u.has_key('_is_super_user')

        assert not u.perms
        assert not u.has_key('perms')

        assert not u._messages
        assert not u.has_key('_messages')

    def test_perms(self):
        u = User()
        assert not u.has_perm('foobar')
        u.add_perm('foobar')
        assert u.has_perm('foobar')

        assert not u.has_any_perm('baz', 'zip')
        assert not u.has_any_perm(('baz', 'zip'))
        assert u.has_any_perm('baz', 'foobar')
        assert u.has_any_perm('foobar', 'baz')
        assert u.has_any_perm(('baz', 'foobar'))
        assert u.has_any_perm(['foobar', 'baz'])

    def test_super_user_perms(self):
        u = User()
        u.is_super_user = True
        assert u.is_super_user
        assert u.has_perm('foobar')
        u.add_perm('foobar')
        assert u.has_perm('foobar')

        assert u.has_any_perm('baz', 'zip')
        assert u.has_any_perm('foobar', 'baz')

    def test_get_set_properties(self):
        u = User()
        assert not u.is_authenticated
        u.is_authenticated = True
        assert u.is_authenticated

        u = User()
        assert not u.is_super_user
        u.is_super_user = True
        assert u.is_super_user

    def test_repr(self):
        u = User()
        assert repr(u)

class TestUserProxy(object):

    def test_bool_value(self):
        # make sure UserProxy._current_obj() returns a SOP with the real
        # User behind it instead of returning the real User instance.
        u = UserProxy()
        if not u:
            assert False, 'expected user'
