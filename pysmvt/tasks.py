from decorator import decorator
from pysutils import tolist, OrderedDict
from pysmvt.utils import gather_objects

def _attributes(f, *args, **kwargs):
    """
        does the work of calling the function decorated by `attributes`
    """
    return f(*args, **kwargs)

def attributes(*args):
    """
        a decorator to add an "attribute" to an action, which can be used
        as a filtering mechanism to control what actions in given task are run.
        If we have the following in tasks.init_data:
        
            @attributes('test', 'dev')
            def action_020_a_little_data():
                pass
            
            @attributes('prod')
            def action_020_a_lot_of_data():
                pass
            
        Given the above, then:
            
            run_tasks('init-data') # both functions called
            run_tasks('init-data:prod') # only action_020_a_lot_of_data
            run_tasks('init-data:test') # only action_020_a_little_data
            run_tasks('init-data:dev') # only action_020_a_little_data
            run_tasks('init-data:foo') # neither function called
        
    """
    def decorate_func(f):
        if args:
            f.__pysmvt_task_attrs = args
        return decorator(_attributes, f)
    return decorate_func


def run_tasks(tasks, print_call=True, *args, **kwargs):
    tasks = tolist(tasks)
    retval = OrderedDict()
    for task in tasks:
        # split off the attribute if it is present:
        if ':' in task:
            task, attr = task.split(':', 1)
        else:
            attr = None
        # allow tasks to be defined with dashes, but convert to
        # underscore to follow file naming conventions
        underscore_task = task.replace('-', '_')
        
        modlist = gather_objects('tasks.%s' % underscore_task)
        
        callables = []
        for modobjs in modlist:
            for k,v in modobjs.iteritems():
                # do prep work for testing the callable's attributes
                if attr is None:
                    has_attr = True
                else:
                    callable_attrs = getattr(v, '__pysmvt_task_attrs', tuple())
                    has_attr = attr in callable_attrs

                if k.startswith('action_') and has_attr:
                    # function name, module name, function object
                    # we added module name as the second value for 
                    # sorting purposes, it gives us a predictable
                    # order
                    callables.append((k, modobjs['__name__'], v, None))
        retval[task] = []
        for call_tuple in sorted(callables):
            if print_call == True:
                print '--- Calling: %s:%s ---' % (call_tuple[1], call_tuple[0])
            retval[task].append((
                call_tuple[0], 
                call_tuple[1], 
                call_tuple[2]()
                ))
    return retval
                    
