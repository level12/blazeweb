from blinker import Namespace

from pysmvt import ag

def signal(name, doc=None):
    return ag.events_namespace.signal(name, doc)
