from nose.tools import eq_
from pysmvt.tasks import run_tasks
from pysmvt import getview

# create the wsgi application that will be used for testing
from pysmvttestapp.applications import make_wsgi
    
class TestTasks(object):
    
    @classmethod
    def setup_class(cls):
       make_wsgi('Testruns')

    def test_task(self):
        assert run_tasks(('init-db', 'init-data'), print_call=False) == \
        {'init-db': [
                ('action_000', 'pysmvttestapp.tasks.init_db', 'pysmvttestapp.tasks.init_db'), 
                ('action_001', 'pysmvttestapp.modules.routingtests.tasks.init_db', 'pysmvttestapp.modules.routingtests.tasks.init_db'), 
                ('action_001', 'pysmvttestapp.modules.tests.tasks.init_db', 'pysmvttestapp2.modules.tests.tasks.init_db'), 
                ('action_001', 'pysmvttestapp.tasks.init_db', 'pysmvttestapp.tasks.init_db'), 
                ('action_002', 'pysmvttestapp.tasks.init_db', 'pysmvttestapp.tasks.init_db'),
            ],
        'init-data': [
                ('action_010', 'pysmvttestapp.tasks.init_data', 'lots of data'), 
            ],
        }
    
    def test_notask(self):
        eq_(run_tasks('not-there', print_call=False), {'not-there': []})
        
    def test_single_attribute(self):
        assert run_tasks('init-db:test', print_call=False) == \
        {'init-db': [
                ('action_001', 'pysmvttestapp.tasks.init_db', 'pysmvttestapp.tasks.init_db'),
            ],
        }
        
    def test_multiple_attributes(self):
        assert run_tasks('init-db:prod', print_call=False) == \
        {'init-db': [
                ('action_000', 'pysmvttestapp.tasks.init_db', 'pysmvttestapp.tasks.init_db'), 
                ('action_002', 'pysmvttestapp.tasks.init_db', 'pysmvttestapp.tasks.init_db'),
            ],
        }
        
    def test_matrix_noattr(self):
        eq_(run_tasks('attr-matrix', print_call=False),
        {'attr-matrix': [
                ('action_1noattr', 'pysmvttestapp.tasks.attr_matrix', None),
                ('action_2xattr', 'pysmvttestapp.tasks.attr_matrix', None),
                ('action_4mxattr', 'pysmvttestapp.tasks.attr_matrix', None),
                ('action_5yattr', 'pysmvttestapp.tasks.attr_matrix', None),
                ('action_7myattr', 'pysmvttestapp.tasks.attr_matrix', None),
            ],
        })
        
    def test_matrix_attr(self):
        eq_(run_tasks('attr-matrix:xattr', print_call=False),
        {'attr-matrix': [
                ('action_2xattr', 'pysmvttestapp.tasks.attr_matrix', None),
                ('action_3pxattr', 'pysmvttestapp.tasks.attr_matrix', None),
            ],
        })
        
    def test_matrix_soft_attr(self):
        eq_(run_tasks('attr-matrix:~xattr', print_call=False),
        {'attr-matrix': [
                ('action_1noattr', 'pysmvttestapp.tasks.attr_matrix', None),
                ('action_2xattr', 'pysmvttestapp.tasks.attr_matrix', None),
                ('action_3pxattr', 'pysmvttestapp.tasks.attr_matrix', None),
                ('action_5yattr', 'pysmvttestapp.tasks.attr_matrix', None),
                ('action_7myattr', 'pysmvttestapp.tasks.attr_matrix', None),
            ],
        })

