#!/usr/bin/env python
# -*- coding: utf-8 -*-
#import dbgp.client
#dbgp.client.brk(host="localhost", port=3800)

import rcsutils

# setup the virtual environment so that we can import specific versions
# of system libraries and can also import from our local libs directory 
rcsutils.setup_virtual_env('pysmvt-libs-trunk', __file__)

# At this point, all of the libraries in our virtual env should be available,
# lets get started by importing all our "action" functions to make them available
from pysmvt.script import *

# this function has to be defined and should return an instantiated PySMVT
# application class
def make_app():
    from pysmvttestapp.application import Webapp
    return Webapp('Testruns')

def action_printpath():
    import sys
    from rcsutils import pprint
    app = make_app()
    app.bind_to_context()
    app.loader.app_names('modules')
    #pprint(sys.path)
    

# main routine called when this module (file) is called directly
# like:
# > python manage.py
if __name__ == '__main__':
    script.run()
