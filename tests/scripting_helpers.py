from os import environ, path

from scripttest import TestFileEnvironment

here = path.dirname(path.abspath(__file__))
script_test_path = path.join(here, 'test-output')
apps_path = path.join(here, 'apps')
base_environ = environ.copy()
base_environ['PYTHONPATH'] = apps_path
env = TestFileEnvironment(script_test_path, environ=base_environ)