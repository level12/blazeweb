def pytest_addoption(parser):
    parser.addoption("--blazeweb_package", action="store",
                     help="blazeweb-package: app module to run for tests")
    parser.addoption("--blazeweb_profile", action="store", default="Test",
                     help="blazeweb-profile: app settings profile to use (default is Test)")


def pytest_configure(config):
    from blazeutils import tolist
    from blazeweb.events import signal
    from blazeweb.globals import ag, settings
    from blazeweb.hierarchy import findobj
    from blazeweb.scripting import load_current_app
    _, _, _, wsgiapp = load_current_app(config.getoption('blazeweb_package'),
                                        config.getoption('blazeweb_profile'))

    # make the app available to the tests
    ag.wsgi_test_app = wsgiapp

    # an application can define functions to be called after the app
    # is initialized but before any test inspection is done or tests
    # are ran.  We call those functions here:
    for callstring in tolist(settings.testing.init_callables):
        tocall = findobj(callstring)
        tocall()

    # we also support events for pre-test setup
    signal('blazeweb.pre_test_init').send()
