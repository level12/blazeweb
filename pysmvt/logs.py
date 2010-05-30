from os import path
import logging
from logging.handlers import RotatingFileHandler
APPLICATION = 25

class Logger(logging.Logger):
    
    def application(self, msg, *args, **kwargs):
        """
            a convenience function for logging messages at level 25, which
            is the "application" level for the pysmvt framework.  This level is
            intended to be used for application level information and is
            not used by the pysmvt framework.  An example of its intended
            use would be to log the IP address of each user logging in.
        """
        return self.log(APPLICATION, msg, *args, **kwargs)

logging.setLoggerClass(Logger)
logging.addLevelName(APPLICATION, 'APPLICATION')

def _create_handlers_from_settings(settings):
    """
        used internally to setup logging for the settings.logs
    """
    # clear any previously setup handlers
    clear_settings_handlers()
    
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
        error_handler._from_pysmvt_settings = True
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
        app_handler._from_pysmvt_settings = True
        app_handler.setLevel(APPLICATION)
        app_handler.setFormatter(formatter)
        app_handler.addFilter(OnlyLevel25())
        logging.root.addHandler(app_handler)
    
    # add a null handler so that we don't get the "no handlers could be found"
    # error message
    if settings.logs.null_handler.enabled:
        class NullHandler(logging.Handler):
            
            _from_pysmvt_settings = True
            
            def emit(self, record):
                pass
        logging.root.addHandler(NullHandler())


def clear_settings_handlers():
    new_handlers = []
    for h in logging.root.handlers:
        if getattr(h, '_from_pysmvt_settings', False):
            h.flush()
            h.close()
        else:
            new_handlers.append(h)
    logging.root.handlers = new_handlers