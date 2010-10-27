from blazeweb.views import asview

@asview('/news')
def newsindex():
    return 'min2 news index'
