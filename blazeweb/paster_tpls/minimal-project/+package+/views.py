from blazeweb.views import asview

@asview('/')
def index():
    return 'index'

@asview()
def broke():
    # this is here so you can see the email/logging that happens if your
    # app has an exception
    foo = bar
