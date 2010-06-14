from pysmvt.views import asview

@asview('/news/display')
def display():
    return 'np4 display'
