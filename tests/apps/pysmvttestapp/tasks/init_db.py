from pysmvt.tasks import attributes

loc = 'pysmvttestapp.tasks.init_db'

@attributes('dev', 'prod')
def action_000():
    return loc

@attributes('test')
def action_001():
    return loc

@attributes('prod')
def action_002():
    return loc

