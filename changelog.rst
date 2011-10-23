Change Log
----------

0.4.3 released 2011-10-22
=========================

* add routing.abs_static_url(), is available in the template too
* jinja.Translator can now render strings: ag.tplengine.render_string(...)
* change requirement in setup.py for minimock now that 1.2.7 has been released
* detect BW_STORAGE_DIR environ variable

0.4.2 released 2011-06-11
=========================

* fix bug in UserProxy

0.4.1 released 2011-06-11
=========================

* fixed `bw project` command, it will now create a decent project file/folder
  skeleton, see example below.
* minimock's 1.2.6 release breaks some usage of the library, "pin" dependency at
  1.2.5
* add config option http_exception_handling, default behavior is unchanged
* add testing.runview() to make it easier to test views without a WSGI test
  runner (Werkzeug Client, WebTest TestApp)

Project skeleton will look like::

    foobar-dist/
    |-- changelog.rst
    |-- foobar
    |   |-- application.py
    |   |-- config
    |   |   |-- __init__.py
    |   |   |-- settings.py
    |   |   `-- site_settings.py
    |   |-- __init__.py
    |   |-- templates
    |   |   `-- index.html
    |   |-- tests
    |   |   |-- __init__.py
    |   |   `-- test_views.py
    |   `-- views.py
    |-- MANIFEST.in
    |-- readme.rst
    `-- setup.py

0.4.0 released 2011-03-01
=========================

* BC BREAK: adjustments to session management & user objects so sessions are
  lazily loaded.  See commits [527b5279ce16], [ae2f4d5c6789] for details of BC
  issues.
* add utils.session_regenerate_id()


0.3.3 released 2011-02-11
=========================

* added a new log, on by default, to capture details about sent emails
* added warning level logs when mail_programmers() or mail_admins() is
  used with an empty setting

0.3.2 released 2011-02-04
=========================

* added pass_as parameter to View.add_processor()
* bump up the default settings for logs.max_bytes(50MB) and log.backup_count (10)
* add settings_connect() decorator for connecting events to settings instance methods
* added setup_*_logging() methods
* make the user and session object available to test responses
