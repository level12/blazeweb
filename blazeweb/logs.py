from os import path
import logging
from blazeweb.globals import settings
from logging.handlers import RotatingFileHandler
APPLICATION = 25

class Logger(logging.Logger):

    def application(self, msg, *args, **kwargs):
        """
            a convenience function for logging messages at level 25, which
            is the "application" level for the blazeweb framework.  This level is
            intended to be used for application level information and is
            not used by the blazeweb framework.  An example of its intended
            use would be to log the IP address of each user logging in.
        """
        return self.log(APPLICATION, msg, *args, **kwargs)

logging.setLoggerClass(Logger)
logging.addLevelName(APPLICATION, 'APPLICATION')

def create_handlers_from_settings(settings):
    """
        used internally to setup logging for the settings.logs
    """
    # clear any previously setup handlers
    clear_settings_handlers()

    if not settings.logs.enabled:
        return

    # have to set the root logger lower than WARN (the default) or our
    # application logs will never be seen
    logging.root.setLevel(APPLICATION)

    if settings.logs.errors.enabled:
        format_str = "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
        formatter = logging.Formatter(format_str)

        error_handler = RotatingFileHandler(
              path.join(settings.dirs.logs, 'errors.log'),
              maxBytes=settings.logs.max_bytes,
              backupCount=settings.logs.backup_count,
        )
        error_handler._from_blazeweb_settings = True
        error_handler.setLevel(logging.WARN)
        error_handler.setFormatter(formatter)
        logging.root.addHandler(error_handler)

    if settings.logs.application.enabled:
        class OnlyLevel25(logging.Filter):
            def filter(self, record):
                 return record.levelno == 25

        format_str = "%(asctime)s - %(name)s - %(message)s"
        formatter = logging.Formatter(format_str)

        app_handler = RotatingFileHandler(
              path.join(settings.dirs.logs, 'application.log'),
              maxBytes=settings.logs.max_bytes,
              backupCount=settings.logs.backup_count,
        )
        app_handler._from_blazeweb_settings = True
        app_handler.setLevel(APPLICATION)
        app_handler.setFormatter(formatter)
        app_handler.addFilter(OnlyLevel25())
        logging.root.addHandler(app_handler)

    if settings.logs.email.enabled:
        format_str = "%(asctime)s - %(message)s"
        formatter = logging.Formatter(format_str)

        app_handler = RotatingFileHandler(
              path.join(settings.dirs.logs, 'email.log'),
              maxBytes=settings.logs.max_bytes,
              backupCount=settings.logs.backup_count,
        )
        app_handler._from_blazeweb_settings = True
        app_handler.setLevel(logging.INFO)
        app_handler.setFormatter(formatter)
        logging.getLogger('blazeweb.mail').addHandler(app_handler)
        logging.getLogger('blazeweb.mail').setLevel(logging.INFO)

def clear_settings_handlers():
    new_handlers = []
    for h in logging.root.handlers:
        if getattr(h, '_from_blazeweb_settings', False):
            h.flush()
            h.close()
        else:
            new_handlers.append(h)
    logging.root.handlers = new_handlers

    # add a null handler so that we don't get the "no handlers could be found"
    # error message
    if settings.logs.null_handler.enabled:
        class NullHandler(logging.Handler):

            _from_blazeweb_settings = True

            def emit(self, record):
                pass
        logging.root.addHandler(NullHandler())

def setup_handler_logging(handler, level, *loggers):
    for lname in loggers:
        logger = logging.getLogger(lname)
        logger.addHandler(handler)
        logger.setLevel(level)

def setup_file_logging(fname, level, *loggers, **kwargs):
    loc_settings = kwargs.pop('settings', None) or settings
    format_str = kwargs.pop('format_str', None) or "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
    max_bytes = kwargs.pop('max_bytes', None) or loc_settings.logs.max_bytes
    backup_count = kwargs.pop('backup_count', None) or loc_settings.logs.backup_count

    formatter = logging.Formatter(format_str)

    handler = RotatingFileHandler(
              path.join(loc_settings.dirs.logs, fname),
              maxBytes = max_bytes,
              backupCount = backup_count,
        )
    handler.setLevel(level)
    handler.setFormatter(formatter)

    setup_handler_logging(handler, level, *loggers)

def setup_stdout_logging(level, *loggers, **kwargs):
    format_str = kwargs.pop('format_str', None) or "%(name)s - %(message)s"
    formatter = logging.Formatter(format_str)

    handler = logging.StreamHandler()
    handler.setLevel(level)
    handler.setFormatter(formatter)

    setup_handler_logging(handler, level, *loggers)
