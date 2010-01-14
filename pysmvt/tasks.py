from pysutils import tolist, OrderedDict
from pysmvt.utils import gather_objects

def run_tasks(tasks, print_call=True, *args, **kwargs):
    tasks = tolist(tasks)
    retval = OrderedDict()
    for task in tasks:
        # allow tasks to be defined with dashes, but convert to
        # underscore to follow file naming conventions
        underscore_task = task.replace('-', '_')
        
        modlist = gather_objects('tasks.%s' % underscore_task)
        
        callables = []
        for modobjs in modlist:
            for k,v in modobjs.iteritems():
                if k.startswith('action_'):
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
                    
