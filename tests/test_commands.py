import os
from nose.plugins.skip import SkipTest
from nose.tools import eq_

from blazeutils.config import QuickSettings
from blazeutils.helpers import tolist

from scripting_helpers import env, script_test_path, here, is_win

def run_application(testapp, *args, **kw):
    cwd = os.path.join(here, 'apps', testapp)
    application_file = 'application.py'
    args = ('python', application_file) + args
    env.clear()
    kw.setdefault('cwd', cwd)
    result = env.run(*args, **kw)
    return result

def run_blazeweb(*args, **kw):
    args = ('bw',) + args
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
    assert 'tasks' in result.stdout
    assert 'shell' in result.stdout
    assert 'static-copy' in result.stdout
    assert 'component-map' in result.stdout, result.stdout

def test_bad_profile():
    result = run_application('minimal2', '-p', 'profilenotthere', expect_error = True)
    assert 'settings profile "profilenotthere" not found in this application' in result.stderr, result.stderr

def test_blazeweb_usage():
    result = run_blazeweb()
    script_name = 'bw-script.py' if is_win else 'bw'
    assert 'Usage: ' + script_name + ' [global_options] COMMAND [command_options]' in result.stdout, result.stdout
    assert 'SETTINGS_PROFILE' not in result.stdout
    assert 'jinja-convert' in result.stdout

def test_app_testrun():
    indexstr = '\nindex\n'
    res = run_application('minimal2', 'testrun')
    assert '200 OK' in res.stdout
    assert 'Content-Type: text/html' in res.stdout
    assert indexstr in res.stdout.replace('\r\n', '\n'), res.stdout.__repr__()

    res = run_application('minimal2', 'testrun', '--silent')
    assert '200 OK' not in res.stdout
    assert 'Content-Type: text/html' not in res.stdout
    assert indexstr not in res.stdout.replace('\r\n', '\n')

    indexstr2 = 'index\n'
    res = run_application('minimal2', 'testrun', '--no-headers')
    assert '200 OK' not in res.stdout
    assert 'Content-Type: text/html' not in res.stdout
    assert indexstr2 in res.stdout.replace('\r\n', '\n'), res.stdout

    res = run_application('minimal2', 'testrun', '--no-body')
    assert '200 OK' in res.stdout
    assert 'Content-Type: text/html' in res.stdout
    assert indexstr not in res.stdout.replace('\r\n', '\n')

def test_app_tasks():
    res = run_application('minimal2', 'tasks', expect_error=True)
    assert 'You must provide at least 1 argument' in res.stdout

    res = run_application('minimal2', 'tasks', 'notasksthere')
    assert res.stdout.strip() == '', res.stdout

    res = run_application('minimal2', 'tasks', 'init_data')
    assert 'appstack.tasks.init_data:action_010' in res.stdout, res
    assert 'doit' in res.stdout

    res = run_application('minimal2', 'tasks', 'init_data', '-t')
    assert 'appstack.tasks.init_data:action_010' in res.stdout
    assert 'doit' not in res.stdout

def test_app_routes():
    res = run_application('minimal2', 'routes')
    assert "'/'" in res.stdout, res.stdout

class TestProjectCommands(object):
    def check_command(self, projname, template, file_count, look_for, expect_stderr=False):
        res = env.run('pip', 'uninstall', projname, '-y', expect_error=True)
        assert 'not installed' in res.stdout or 'Succesfully uninstalled' in res.stdout
        if template is not None:
            result = run_blazeweb('project', '-t', template, '--no-interactive', projname)
        else:
            result = run_blazeweb('project', '--no-interactive', projname)
        eq_( len(result.files_created), file_count)
        setup_args = ['python', 'setup.py', 'develop']
        if is_win:
            # running setup.py on the new project causes the .exe scripts to be
            # recreated.  This includes the nosetests.exe file.  But in windows
            # we are using that file to run the tests that are running this code
            # and that causes a permission denied error.  Therefore, we need to
            # prevent the setup.py develop command from checking dependencies.
            setup_args.append('-N')
        env.run(cwd=os.path.join(script_test_path, projname + '-dist'), expect_stderr=expect_stderr,
                *setup_args)
        res = env.run(projname)
        script_name = '%s-script.py' % projname if is_win else projname
        assert 'Usage: %s [global_options]' % script_name in res.stdout, res.stdout
        res = env.run(projname, 'testrun')
        assert '200 OK' in res.stdout
        assert 'Content-Type: text/html' in res.stdout
        indexstr = '\n%s\n' % look_for
        assert indexstr in res.stdout
        res = env.run('pip', 'uninstall', projname, '-y')
        assert 'Successfully uninstalled' in res.stdout.replace('\r\n', '\n'), res.stdout
        env.clear()

    def test_minimal(self):
        self.check_command('minimalproj_from_bw_tests', 'minimal', 9, 'index', expect_stderr=True)

    def test_bwproject(self):
        self.check_command('bwproj_from_bw_tests', 'bwproject', 18, 'Hello World')

    def test_default(self):
        # should be bwproject
        self.check_command('bwproj_from_bw_tests', None, 18, 'Hello World')
