Change Log
===========

0.3.3 released 2011-02-11
-----------------------------
 - added a new log, on by default, to capture details about sent emails
 - added warning level logs when mail_programmers() or mail_admins() is
    used with an empty setting

0.3.2 released 2011-02-04
-----------------------------

 - added pass_as parameter to View.add_processor()
 - bump up the default settings for logs.max_bytes(50MB) and log.backup_count (10)
 -  add settings_connect() decorator for connecting events to settings instance methods
 - added setup_*_logging() methods
 - make the user and session object available to test responses
