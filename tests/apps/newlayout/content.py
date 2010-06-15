from blazeweb.content import Content

class HelloWorld(Content):

  def create(self, name=u'world'):
    return u'hello %s' % name
