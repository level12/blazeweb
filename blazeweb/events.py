from blinker import Namespace

from blazeweb.globals import ag

def signal(name, doc=None):
    return ag.events_namespace.signal(name, doc)
