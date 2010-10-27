import os

from scripttest import TestFileEnvironment

from blazeweb.routing import current_url
from blazeweb.testing import inrequest
from scripting_helpers import env, here, script_test_path, base_environ, apps_path

import config
from newlayout.application import make_wsgi

def setup_module():
   make_wsgi()

# call test_currenturl() with a fake request setup.  current_url()
# depends on a correct environment being setup and would not work
# otherwise.
@inrequest()
def test_currenturl():
    assert current_url(host_only=True) == 'http://localhost/'

class TestThis(object):
    """ Works for class methods too """

    @inrequest()
    def test_currenturl(self):
        assert current_url(host_only=True) == 'http://localhost/'

def test_nose_component_app_package_find_by_directory():
    cwd = os.path.join(here, 'apps', 'minimal2')
    res = env.run('nosetests', expect_error=True, cwd=cwd)
    assert 'Ran 1 test in' in res.stderr, res.stderr
    assert 'OK' in res.stderr, res.stderr

def test_nose_component_disable():
    cwd = os.path.join(here, 'apps', 'minimal2')
    res = env.run('nosetests', '--blazeweb-disable', expect_error=True, cwd=cwd)
    assert 'No object (name: ag) has been registered for this thread' in res.stderr, res.stderr

def test_nose_component_app_package_by_command_line():
    res = env.run('nosetests', 'minimal2', expect_error=True, cwd=apps_path)
    assert 'No object (name: ag) has been registered for this thread' in res.stderr, res.stderr

    res = env.run('nosetests', '--blazeweb-package=minimal2', 'minimal2', expect_error=True, cwd=apps_path)
    assert 'Ran 1 test in' in res.stderr, res.stderr
    assert 'OK' in res.stderr

def test_nose_component_app_package_by_environ():
    base_environ['BLAZEWEB_APP_PACKAGE'] = 'minimal2'
    newenv = TestFileEnvironment(script_test_path, environ=base_environ)
    res = newenv.run('nosetests', 'minimal2', expect_error=True, cwd=apps_path)
    assert 'Ran 1 test in' in res.stderr, res.stderr
    assert 'OK' in res.stderr, res.stderr

def test_nose_component_profile_choosing():
    cwd = os.path.join(here, 'apps', 'minimal2')

    # default Test profile
    res = env.run('nosetests', '-s', expect_error=True, cwd=cwd)
    assert 'Ran 1 test in' in res.stderr
    assert 'OK' in res.stderr
    assert 'Test settings' in res.stdout

    # profile by command line
    res = env.run('nosetests', '-s', '--blazeweb-profile=Test2', expect_error=True, cwd=cwd)
    assert 'Ran 1 test in' in res.stderr
    assert 'OK' in res.stderr
    assert 'Test2 settings' in res.stdout
