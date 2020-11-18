import platform
from shutil import rmtree
from os import environ, path
import time

from scripttest import TestFileEnvironment

is_win = platform.system() == 'Windows'

here = path.dirname(path.abspath(__file__))
script_test_path = path.join(here, 'test-output')

# clear the test folder since other apps use this output folder as a temporary
# folder; it might be created already, in which case scriptest bombs. A simple rmtree
# will work in *nix, but Windows will often hang on to files in a folder while it is
# being cleaned up, so we need to have a retry mechanism.
count = 0
while True:
    try:
        rmtree(script_test_path)
        break
    except OSError:
        count += 1
        if count == 10:
            raise
        time.sleep(0.1)

apps_path = path.join(here, 'apps')
base_environ = environ.copy()
base_environ['PYTHONPATH'] = apps_path

if not is_win:
    class BWTestFileEnvironment(TestFileEnvironment):
        def clear(self, force=True):
            super(BWTestFileEnvironment, self).clear(force=force)
else:
    # Windows throws scripttest some curveballs when it comes to cleaning up folders. Use force
    # on clear to prevent scripttest checking to see if it created the directory (since we know
    # what path we are working with, beware if you put things there that don't go there). Then,
    # we would still get WindowsError exceptions, so have a retry with a short delay to resolve.
    class BWTestFileEnvironment(TestFileEnvironment):
        def clear(self):
            count = 0
            while True:
                try:
                    super(BWTestFileEnvironment, self).clear(force=True)
                    break
                except WindowsError as e:
                    if 'another process' in str(e) and 'email.log' in str(e):
                        break
                    count += 1
                    if count == 10:
                        raise
                    time.sleep(0.1)
env = BWTestFileEnvironment(script_test_path, environ=base_environ)
