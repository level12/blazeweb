Change Log
----------

0.4.15 released 2016-06-03
==========================

* fixed unicode handling for JSON parsing

0.4.14 released 2015-12-08
==========================

* add py.test plugin to load a blaze app for testing, similar to the nose plugin

0.4.13 released 2015-10-23
==========================

* exception_with_context() is now filtered for sensitive information.  The filters can be
  controlled through settings.

0.4.12 released 2015-10-23
==========================

* add json filter, support all json mimetypes that webtest does in the Request.json property

0.4.11 released 2014-12-08
==========================

* add FileResponse

0.4.10 released 2014-09-18
==========================

* added relative_path kwarg to link_css_url and source_js_url, default behavior
  remains to use abs_static_url on the url

0.4.9 released 2014-08-29
=========================

* add auto-cleanup of beaker sessions for file/dbm storage (if applicable).
  settings.beaker.auto_clear_sessions (default True) controls this function
* cleanup setup.py and add version.txt file, move to "extra_requires" for specifying developer
  dependencies.

0.4.8 released 2013-12-17
=========================

* adjust setup_file_logging() to accept an argument for the settings object

0.4.7 released 2012-10-24
=========================

* add extra_context argument to View.render_json()

0.4.6 released 2012-07-16
=========================

* Fixed 0.4.5 regression: previously, a POST XHR would try for xhr() and then
  post() on a view class, but 0.4.5 would only try for xhr().

0.4.5 released 2012-07-09
=========================

* add include_rst() and include_mkdn() as functions available in Jinja templates
* css and js from included templates is now always included, regardless of where
  in the child template the include method is called.
* add "content" template filter which will merge css/js from the given content
  object into the parent template
* add link_css_url(), source_js_url() and complimentary head_link_tags() and
  head_script_tags() template functions to be able to include CSS/JS URLs from
  any template.
* make HTTP request method handling more robust.  Its now easier to respond to
  request methods that are not GET/POST and we will now correctly return a 405
  Method Not Allowed response when the view can not handle the request method
  sent over.

0.4.4 released 2011-11-09
=========================

* fix a nasty bug in the View arg processing that can alter formencode validator
    classes

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
