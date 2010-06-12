from pysmvt import rg
from pysmvt.views import asview
from pysmvt.wrappers import Response

@asview('/')
def index():
    return 'index'
