from blazeweb.globals import ag, settings

def signal(name, doc=None):
    return ag.events_namespace.signal(name, doc)

def settings_connect(signalname):
    """
        used on setting methods to connect them to signals in such a way
        that does not give us problems when importing the settings module.

        When the decorated method is called b/c the event fires,
        it will be sent two parameters: self & sender.  Self is the instance
        of the settings class and sender is the event's sender.
    """
    def the_decorator(method):
        return SettingsConnectHelper(signalname, method)
    return the_decorator

class SettingsConnectHelper(object):

    def __init__(self, signalname, method):
        self.signalname = signalname
        self.method = method

    def __call__(self, signal_sender):
        real_settings = settings._current_obj()
        self.method(real_settings, signal_sender)

    def connect(self):
        """ called by the appliation's init_settings() """
        # keep a reference to the signal so it doesn't get garbage
        # collected
        self.signal = signal(self.signalname)
        self.signal.connect(self)


def clear_old_beaker_sessions(sender):
    # for dbm and file type beaker sessions, files are cached under data_dir
    #   use the last-accessed time to determine which to prune
    if settings.beaker.type in ('dbm', 'file') and settings.beaker.auto_clear_sessions:
        if not hasattr(settings.beaker, 'timeout'):
            return

        import datetime as dt
        import os
        session_path = settings.beaker.data_dir
        cutoff = (
            dt.datetime.now() -
            dt.timedelta(seconds=settings.beaker.timeout)
        )

        for root, dirnames, filenames in os.walk(session_path):
            for filename in filenames:
                session_file = os.path.join(root, filename)
                if dt.datetime.fromtimestamp(
                    os.stat(session_file).st_atime
                ) < cutoff:
                    os.remove(session_file)
