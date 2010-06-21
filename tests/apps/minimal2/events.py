from blazeweb.globals import rg
from blazeweb.events import signal

def fire_after_event_init(sender):
    return 'minimal2'
signal('blazeweb.events.initialized').connect(fire_after_event_init)

def modify_response(sender, response=None):
    if 'eventtest' in rg.request.url:
        response.data = response.data + 'minimal2'
signal('blazeweb.response_cycle.ended').connect(modify_response)
