from blazeweb.views import asview

@asview('/news/display')
def display():
    return 'np4 display'
