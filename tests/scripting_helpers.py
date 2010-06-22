import platform
from shutil import rmtree
from os import environ, path

from scripttest import TestFileEnvironment

if 'Windows' == platform.system():
    is_win = True
else:
    is_win = False

here = path.dirname(path.abspath(__file__))
script_test_path = path.join(here, 'test-output')

# clear the test folder since other apps use this output folder as a temporary
# folder; it might be created already, in which case scriptest bombs
rmtree(script_test_path)

apps_path = path.join(here, 'apps')
base_environ = environ.copy()
base_environ['PYTHONPATH'] = apps_path
env = TestFileEnvironment(script_test_path, environ=base_environ)
