from nose.tools import eq_
from pysmvt.tasks import run_tasks
from pysmvt import getview

# create the wsgi application that will be used for testing
import config
from pysmvttestapp.applications import make_wsgi

class TestTasks(object):

    @classmethod
    def setup_class(cls):
       make_wsgi('Testruns')

    def test_task(self):
        eq_( run_tasks(('init-db', 'init-data'), print_call=False),
        {'init-db': [
                ('action_000', 'appstack.tasks.init_db', 'pysmvttestapp.tasks.init_db'),
                ('action_001', 'appstack.tasks.init_db', 'pysmvttestapp.tasks.init_db'),
                ('action_001', 'plugstack.routingtests.tasks.init_db', 'pysmvttestapp.plugins.routingtests.tasks.init_db'),
                ('action_001', 'plugstack.tests.tasks.init_db', 'pysmvttestapp2.plugins.tests.tasks.init_db'),
                ('action_002', 'appstack.tasks.init_db', 'pysmvttestapp.tasks.init_db'),
                ('action_003', 'plugstack.routingtests.tasks.init_db', 'pysmvttestapp2.plugins.routingtests.tasks.init_db'),
                ('action_005', 'appstack.tasks.init_db', 'pysmvttestapp2.tasks.init_db'),
            ],
        'init-data': [
                ('action_010', 'appstack.tasks.init_data', 'lots of data'),
            ],
        })

    def test_notask(self):
        eq_(run_tasks('not-there', print_call=False), {'not-there': []})

    def test_single_attribute(self):
        assert run_tasks('init-db:test', print_call=False) == \
        {'init-db': [
                ('action_001', 'appstack.tasks.init_db', 'pysmvttestapp.tasks.init_db'),
            ],
        }

    def test_multiple_attributes(self):
        assert run_tasks('init-db:prod', print_call=False) == \
        {'init-db': [
                ('action_000', 'appstack.tasks.init_db', 'pysmvttestapp.tasks.init_db'),
                ('action_002', 'appstack.tasks.init_db', 'pysmvttestapp.tasks.init_db'),
            ],
        }

    def test_matrix_noattr(self):
        eq_(run_tasks('attr-matrix', print_call=False),
        {'attr-matrix': [
                ('action_1noattr', 'appstack.tasks.attr_matrix', None),
                ('action_2xattr', 'appstack.tasks.attr_matrix', None),
                ('action_4mxattr', 'appstack.tasks.attr_matrix', None),
                ('action_5yattr', 'appstack.tasks.attr_matrix', None),
                ('action_7myattr', 'appstack.tasks.attr_matrix', None),
            ],
        })

    def test_matrix_attr(self):
        eq_(run_tasks('attr-matrix:xattr', print_call=False),
        {'attr-matrix': [
                ('action_2xattr', 'appstack.tasks.attr_matrix', None),
                ('action_3pxattr', 'appstack.tasks.attr_matrix', None),
            ],
        })

    def test_matrix_soft_attr(self):
        eq_(run_tasks('attr-matrix:~xattr', print_call=False),
        {'attr-matrix': [
                ('action_1noattr', 'appstack.tasks.attr_matrix', None),
                ('action_2xattr', 'appstack.tasks.attr_matrix', None),
                ('action_3pxattr', 'appstack.tasks.attr_matrix', None),
                ('action_5yattr', 'appstack.tasks.attr_matrix', None),
                ('action_7myattr', 'appstack.tasks.attr_matrix', None),
            ],
        })
