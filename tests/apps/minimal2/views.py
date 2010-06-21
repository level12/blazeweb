from blazeweb.globals import rg, user
from blazeweb.views import asview, forward
from blazeweb.wrappers import Response

@asview('/')
def index():
    return 'index'

@asview()
def workingview():
    return 'hello foo!'

@asview()
def nosession():
    assert not rg.session
    # but we still have a user object, even though info won't get persisted
    assert user is not None
    return 'hello nosession!'

@asview()
def page1():
    forward('page2')
    return 'hello nosession!'

@asview()
def page2():
    return 'page2!'

@asview()
def hassession():
    assert rg.session
    assert user is not None
    return 'hello hassession!'

@asview()
def session1():
    rg.session['session1'] = 'foo'
    return ''

@asview()
def session2():
    assert rg.session['session1'] == 'foo'
    return ''

@asview()
def session3():
    assert 'session1' not in rg.session
    return ''

@asview()
def eventtest():
    return 'foo'
