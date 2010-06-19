from pysmvt import rg
from pysmvt.events import signal

def fire_after_event_init(sender):
    return 'minimal2'
signal('pysmvt.events.initialized').connect(fire_after_event_init)

def modify_response(sender, response=None):
    if 'eventtest' in rg.request.url:
        response.data = response.data + 'minimal2'
signal('pysmvt.view_returned').connect(modify_response)
