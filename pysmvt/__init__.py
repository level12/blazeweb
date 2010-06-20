try:
    from pysmvt.core import *
except ImportError:
    # this can happen when setup.py is trying to get the version number
    print 'Warning: skipping import errors; this is OK if you are using setup.py'

VERSION = '0.3.0dev'
