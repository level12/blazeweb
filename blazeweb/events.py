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
