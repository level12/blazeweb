from blazeweb.globals import rg
from blazeweb.events import signal
from blazeweb.utils import redirect
from blazeweb.views import forward

def fire_after_event_init(sender):
    return 'newlayout'
signal('blazeweb.events.initialized').connect(fire_after_event_init)

def modify_response(sender, response=None):
    if 'eventtest' in rg.request.url:
        response.data = response.data + 'newlayout'
signal('blazeweb.response_cycle.ended').connect(modify_response)

def send_to_index(sender, endpoint, urlargs):
    """
    simulating hijacking the request and forcing it to go to another view.
    This minicks what you would want to do if a user need to change a password,
    was locked out, or any number of things that might cause you to want to
    send them to a different location than the one they are requesting.
    """
    if 'request-hijack/forward' in rg.request.url:
        # we have to have a flag that says we have already forwarded, otherwise
        # we will get a forward loop since the request isn't modified
        # when we forward
        if getattr(rg, 'newlayout_events_send_to_index', None):
            return
        rg.newlayout_events_send_to_index = True
        forward('Index', tname='index')
    elif 'request-hijack/redirect' in rg.request.url:
        redirect('index/index')
signal('blazeweb.response_cycle.started').connect(send_to_index)
