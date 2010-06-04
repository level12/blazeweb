from pysmvt import rg
from pysmvt.view import asview
from pysmvt.wrappers import Response

@asview('/')
def index():
    return 'index'

