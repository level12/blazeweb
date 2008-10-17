import unittest
import os
import os.path as path
import rcsutils
import config

# setup the virtual environment so that we can import specific versions
# of system libraries but also ensure that our pysmvt module is what
# we are pulling from
rcsutils.setup_virtual_env('pysmvt-libs-trunk', __file__, '..')

from pysmvt import application
from pysmvt.mail import *


class TestMail(unittest.TestCase):
    pass
        
if __name__ == '__main__':
    unittest.main()
