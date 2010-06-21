from decorator import decorator
from blazeutils import tolist, OrderedDict
from blazeweb.hierarchy import gatherobjs

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
            f.__blazeweb_task_attrs = args
        return decorator(_attributes, f)
    return decorate_func


def run_tasks(tasks, print_call=True, test_only=False, *args, **kwargs):
    tasks = tolist(tasks)
    retval = OrderedDict()
    for task in tasks:
        # split off the attribute if it is present:
        if ':' in task:
            task, attr = task.split(':', 1)

            # get the soft attribute flag
            if attr.startswith('~'):
                soft_attribute_matching = True
                attr = attr[1:]
            else:
                soft_attribute_matching = False
        else:
            attr = None

        # allow tasks to be defined with dashes, but convert to
        # underscore to follow file naming conventions
        underscore_task = task.replace('-', '_')

        collection = gatherobjs('tasks.%s' % underscore_task, lambda objname, obj: objname.startswith('action_'))

        callables = []
        for modkey, modattrs in collection.iteritems():
            for actname, actobj in modattrs.iteritems():
                plus_exit = False
                callable_attrs = getattr(actobj, '__blazeweb_task_attrs', tuple())

                # if callable has a "+" attribute
                for cattr in callable_attrs:
                    if cattr.startswith('+') and cattr[1:] != attr:
                        plus_exit = True
                        break

                if plus_exit:
                    continue

                # attribute given, callable is required to have it
                if attr is not None:
                    if soft_attribute_matching:
                        if '-' + attr in callable_attrs:
                            continue
                    elif attr not in callable_attrs and '+' + attr not in callable_attrs:
                        continue

                # function name, module name, function object
                # we added module name as the second value for
                # sorting purposes, it gives us a predictable
                # order
                callables.append((actname, modkey, actobj, None))
        retval[task] = []
        for call_tuple in sorted(callables):
            if print_call == True:
                print '--- Calling: %s:%s ---' % (call_tuple[1], call_tuple[0])
            if test_only:
                callable_retval = 'test_only=True'
            else:
                callable_retval = call_tuple[2]()
            retval[task].append((
                call_tuple[0],
                call_tuple[1],
                callable_retval
                ))
    if print_call and test_only:
        print '*** NOTICE: test_only=True, no actions called ***'
    return retval
