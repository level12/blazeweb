from blazeweb.content import Content
from compstack.nothere import something  # noqa


class Foo(Content):
    def create(self):
        return 'foo'
