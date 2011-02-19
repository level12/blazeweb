from blazeweb.registry import StackedObjectProxy

__all__ = [
    'ag',
    'rg',
    'settings',
    'user',
]

# a "global" object for storing data and objects (like tcp connections or db
# connections) across requests (application scope)
ag = StackedObjectProxy(name="ag")
# the request "global" object, stores data and objects "globaly" during a request.  The
# environment, urladapter, etc. get saved here. (request only)
rg = StackedObjectProxy(name="rg")
# all of the settings data (application scope)
settings = StackedObjectProxy(name="settings")
# the user object (request only)
user = StackedObjectProxy(name="user")
