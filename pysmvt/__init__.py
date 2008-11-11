from paste.registry import StackedObjectProxy

VERSION = '0.1a2'

app = StackedObjectProxy(name="app")
settings = StackedObjectProxy(name="settings")