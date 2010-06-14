from pysmvt import rg, session, user, forward
from pysmvt.views import asview
from pysmvt.wrappers import Response

@asview('/')
def index():
    return 'index'

@asview()
def workingview():
    return 'hello foo!'

@asview()
def nosession():
    assert not session
    # but we still have a user object, even though info won't get persisted
    assert user
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
    assert session
    assert user
    return 'hello hassession!'

@asview()
def session1():
    session['session1'] = 'foo'
    return ''

@asview()
def session2():
    assert session['session1'] == 'foo'
    return ''

@asview()
def session3():
    assert 'session1' not in session
    return ''
