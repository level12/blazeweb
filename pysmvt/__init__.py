from paste.registry import StackedObjectProxy

VERSION = '0.1a2'

# a app "global" object for storing data and objects (like tcp connections or db
# connections) across requests (application scope)
ag = StackedObjectProxy(name="ag")
# the request "global" object, stores data and objects "globaly" during a request.  The
# environment, urladapter, etc. get saved here. (request only)
rg = StackedObjectProxy(name="rco")
# all of the settings data (application scope)
settings = StackedObjectProxy(name="settings")
# the http session (request only)
session = StackedObjectProxy(name="session")
# the user object (request only)
user = StackedObjectProxy(name="user")