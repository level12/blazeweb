import os, sys
from pysutils.config import QuickSettings
from pysutils.helpers import tolist

here = os.path.dirname(os.path.abspath(__file__))
base_path = os.path.join(here, 'test-output')

from scripttest import TestFileEnvironment

env = TestFileEnvironment(base_path)

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
    assert 'testrun' in result.stdout
    
def test_bad_profile():
    result = run_application('minimal2', '-p', 'profilenotthere', expect_error = True)
    assert 'could not find settings profile' in result.stdout
    
def test_pysmvt_usage():
    result = run_pysmvt()
    assert 'Usage: pysmvt [global_options] COMMAND [command_options]' in result.stdout
    assert 'SETTINGS_PROFILE' not in result.stdout
    
def test_pysmvt_project():
    result = run_pysmvt('project', 'foobar', '--no-interactive')
    assert len(result.files_created) > 5

def test_app_testrun():
    res = run_application('minimal2', 'testrun')
    assert '200 OK' in res.stdout
    assert 'Content-Type: text/html' in res.stdout
    assert '\nindex\n' in res.stdout
    
    res = run_application('minimal2', 'testrun', '--silent')
    assert '200 OK' not in res.stdout
    assert 'Content-Type: text/html' not in res.stdout
    assert '\nindex\n' not in res.stdout
    
    res = run_application('minimal2', 'testrun', '--no-headers')
    assert '200 OK' not in res.stdout
    assert 'Content-Type: text/html' not in res.stdout
    assert 'index\n' in res.stdout
    
    res = run_application('minimal2', 'testrun', '--no-body')
    assert '200 OK' in res.stdout
    assert 'Content-Type: text/html' in res.stdout
    assert '\nindex\n' not in res.stdout

def test_minimal_project_checkout_and_functionality():
    projname = 'pysminimalprojtest_no_name_clash_hopefully'
    res = env.run('pip', 'uninstall', projname, '-y', expect_error=True)
    assert 'not installed' in res.stdout or 'Succesfully uninstalled' in res.stdout
    result = run_pysmvt('project', '-t', 'minimal', '--no-interactive', projname)
    assert len(result.files_created) == 9
    env.run('python', 'setup.py', 'develop', cwd=os.path.join(base_path, projname + '-dist'))
    res = env.run(projname)
    assert 'Usage: %s [global_options]' % projname in res.stdout
    res = env.run(projname, 'testrun')
    assert '200 OK' in res.stdout
    assert 'Content-Type: text/html' in res.stdout
    assert '\nindex\n' in res.stdout
    res = env.run('pip', 'uninstall', projname, '-y')
    assert 'Successfully uninstalled' in res.stdout, res.stdout
    env.clear()