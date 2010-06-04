import os, sys
from pysutils.config import QuickSettings
from pysutils.helpers import tolist

here = os.path.dirname(os.path.abspath(__file__))
base_path = os.path.join(here, 'test-scratch')

from scripttest import TestFileEnvironment

env = TestFileEnvironment(os.path.join(here, 'test-output'))

def run_application(testapp, *args, **kw):
    cwd = os.path.join(here, 'apps', testapp)
    application_file = 'application.py'
    args = ('python', application_file) + args
    env.clear()
    kw.setdefault('cwd', cwd)
    result = env.run(*args, **kw)
    return result

def run_pysmvt(*args, **kw):
    args = ('pysmvt',) + args
    env.clear()
    result = env.run(*args, **kw)
    return result

def test_app_usage():
    result = run_application('minimal2')
    assert 'Usage: application.py [global_options] COMMAND [command_options]' in result.stdout, str(result.stdout)
    assert 'SETTINGS_PROFILE' in result.stdout
    assert 'project' not in result.stdout
    assert 'Serve the application' in result.stdout
    
def test_bad_profile():
    result = run_application('minimal2', '-p', 'profilenotthere', expect_error = True)
    assert 'could not find settings profile' in result.stdout
    
def test_pysmvt_usage():
    result = run_pysmvt()
    assert 'Usage: pysmvt [global_options] COMMAND [command_options]' in result.stdout
    assert 'SETTINGS_PROFILE' not in result.stdout
    
def test_pysmvt_project():
    result = run_pysmvt('project', 'foobar', '--no-interactive')
    assert result.files_created > 5
    
    
