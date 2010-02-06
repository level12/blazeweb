from pysmvt.tasks import attributes


def action_1noattr():
    pass

@attributes('xattr')
def action_2xattr():
    pass

@attributes('+xattr')
def action_3pxattr():
    pass

@attributes('-xattr')
def action_4mxattr():
    pass

@attributes('yattr')
def action_5yattr():
    pass

@attributes('+yattr')
def action_6pyattr():
    pass

@attributes('-yattr')
def action_7myattr():
    pass