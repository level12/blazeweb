import __builtin__
import logging
from os import path as ospath
import sys

from blazeutils.datastructures import BlankObject, OrderedDict, UniqueList
from blazeutils.error_handling import raise_unexpected_import_error
from blazeweb.globals import ag, settings
from blazeweb.utils import registry_has_object

log = logging.getLogger(__name__)

class HierarchyImportError(ImportError):
    """
        Used to signal an import error when a request is made to the hierarchy
        tools that can not be filled. Its distinguishable from ImportError so
        that if you receive an ImportError when doing hiearchy processing, you
        know the import error is not from the hierarchy itself but from some
        import in one of the modules the hieararchy lookup accessed.
    """

class FileNotFound(Exception):
    """
        raised when a file is not found in findfile()
    """

class HierarchyManager(object):

    def __init__(self):
        self._builtin_import = __builtin__.__import__
        self.replace_builtin()

    def replace_builtin(self):
        __builtin__.__import__ = self.blazeweb_import
        log.debug('HierarchyManager replaced __builtin__.__import__')

    def restore_builtin(self):
        __builtin__.__import__ = self._builtin_import
        log.debug('HierarchyManager restored __builtin__.__import__')

    def builtin_import(self, name, globals={}, locals={}, fromlist=[], level=-1):
        mod = self._builtin_import(name, globals, locals, fromlist, level)
        # for module reloading purposes in visitmods(), we need to keep track
        # of what application imported a module.  But we only need to do that
        # for modules that are in BlazeWeb applications or are BW components
        if registry_has_object(ag) and registry_has_object(settings):
            # is this module part of the main or supporting app?
            toplevel = name.split('.')[0]
            if toplevel in listapps() or toplevel in list_component_packages():
                mod._blazeweb_hierarchy_last_imported_by = id(ag.app)
        return mod

    def blazeweb_import(self, name, globals={}, locals={}, fromlist=[], level=-1):
        instack_collection = ImportOverrideHelper.doimport(name, fromlist)
        if instack_collection:
            return instack_collection
        return self.builtin_import(name, globals, locals, fromlist, level)
hm = HierarchyManager()

def listapps(reverse=False):
    if reverse:
        apps = list(settings.supporting_apps)
        apps.reverse()
        apps.append(settings.app_package)
        return apps
    return [settings.app_package] + settings.supporting_apps

def listcomponents(reverse=False):
    """
        a flat list of the namespace of each enabled component
    """
    ul = UniqueList()
    for _, pname, _ in list_component_mappings():
        ul.append(pname)
    retval = list(ul)
    if reverse:
        retval.reverse()
    return retval

def list_component_packages():
    """
        a flat list of enabled component packages
    """
    if not hasattr(ag, 'hierarchy_component_packages'):
        packages = []
        for _, _, packagename in list_component_mappings():
            if packagename:
                packages.append(packagename)
        ag.hierarchy_component_packages = packages
    return ag.hierarchy_component_packages

def list_component_mappings(target_component=None, reverse=False, inc_apps=False):
    """
        A list of tuples: (app name, component name, package name)

        The package name will be None if the location of the component is internal
        to the app.
    """
    retval = []
    for app in listapps():
        if inc_apps:
            retval.append((app, None, None))
        acomponents = getattr(settings.componentmap, app)
        for pname in acomponents.keys():
            if target_component is None or pname == target_component:
                for package in acomponents.get_dotted('%s.packages' % pname):
                    retval.append((app, pname, package))
    if reverse:
        retval.reverse()
    return retval

def findcontent(endpoint):
    try:
        return findendpoint(endpoint, 'content')
    except HierarchyImportError, e:
        if not find_exc_is_from(e, endpoint, 'content'):
            raise
        raise HierarchyImportError('An object for Content endpoint "%s" was not found' % endpoint)

def findview(endpoint):
    try:
        return findendpoint(endpoint, 'views')
    except HierarchyImportError, e:
        if not find_exc_is_from(e, endpoint, 'views'):
            raise
        raise HierarchyImportError('An object for View endpoint "%s" was not found' % endpoint)

def find_exc_is_from(e, endpoint, where):
    if ':' not in endpoint:
        component = None,
        attr = endpoint
    else:
        component, attr = endpoint.split(':')
    possible_messages = [
        'module "%s.%s" not found; searched compstack' % (component, where),
        'module "%s" not found; searched appstack' % where,
        'attribute "%s" not found; searched compstack.%s.%s' % (attr, component, where),
        'attribute "%s" not found; searched appstack.%s' % (attr, where),
    ]
    return str(e) in possible_messages

def findendpoint(endpoint, where):
    """
        locate an object in the hierarchy based on an endpoint.  Usage:

        findendpoint('Index', 'views') => from appstack.views import Index
        findendpoint('news:Index', 'views') => from compstack.news.views import Index
        findendpoint('news:Something', 'content') => from compstack.news.content import Something

        Raises: ImportError if view is not found.  But can also raise an
            ImportError if other
    """
    if ':' not in endpoint:
        return AppFinder(where, endpoint).search()
    component, attr = endpoint.split(':')
    return ComponentFinder(component, where, attr).search()

def findfile(endpoint_path):
    """
        locate a file in the hierarchy based on an endpoint and path.  Usage:

        findfile('templates/index.html') could return one of the following:

            .../myapp-dist/myapp/templates/index.html
            .../supportingapp-dist/supportingapp/templates/index.html

        findfile('news:templates/index.html') could return one of the following:

            .../myapp-dist/myapp/components/news/templates/index.html
            .../newscomponent-dist/newscomponent/templates/index.html
            .../supportingapp-dist/supportingapp/components/news/templates/index.html

        Raises: FileNotFound if the path can not be found in the hierarchy
    """
    log.debug('findfile() looking for: %s' % endpoint_path)
    fpath = FileFinderBase.findfile(endpoint_path)
    if not fpath:
        raise FileNotFound('could not find: %s' % endpoint_path)
    return fpath

def findobj(endpoint):
    """
        Allows hieararchy importing based on strings:

        findobject('views.Index') => from appstack.views import Index
        findobject('news:views.Index') => from compstack.news.views import Index
    """
    if '.' not in endpoint:
        raise ValueError('endpoint should have a "."; see docstring for usage')

    if ':' in endpoint:
        component, impname = endpoint.split(':')
        impstring = 'compstack.%s.' % component
    else:
        impname = endpoint
        impstring = 'appstack.'
    parts = impname.split('.')
    attr = parts[-1]
    impname = '.'.join(parts[:-1])
    collector = ImportOverrideHelper.doimport(impstring + impname, [attr])
    return getattr(collector, attr)

def visitmods(dotpath, reverse=False, call_with_mod=None, reloadmod=True):
    """
        Import python modules installed in the appstack or compstack.  Modules
        are visited from the top down.

        reverse: visit modules in the reverse order, from the bottom up
        call_with_mod: a callable that will be called after the module is loaded
            with the loaded module as the only argument to the callable.
        reloadmod: uses reload() on the module if it has already been imported
            by another application; this is useful when loading a module has a
            side-affect and that side-affect needs to be repeated for each app.
            An example of this is when a "views" modules are loaded because they
            use @asview. That decorator, when fired, adds a route in the current
            app to the view. If the views module is shared among more than one
            application running in the same process, an external component for
            example, then that side-affect needs to be repeated for each
            application.
    """
    visitlist = list_component_mappings(inc_apps=True, reverse=reverse)
    for app, pname, package in visitlist:
        try:
            if not pname and not package:
                impstr = '%s.%s' % (app, dotpath)
            elif package:
                impstr = '%s.%s' % (package, dotpath)
            else:
                impstr = '%s.components.%s.%s' % (app, pname, dotpath)
            if sys.modules.has_key(impstr):
                mod_loaded_by = getattr(sys.modules[impstr], '_blazeweb_hierarchy_last_imported_by', None)
                current_app_id = id(ag.app)
                if reloadmod and mod_loaded_by != current_app_id:
                    module = reload(sys.modules[impstr])
                    module._blazeweb_hierarchy_last_imported_by = current_app_id
                else:
                    module = sys.modules[impstr]
            else:
                module = hm.builtin_import(impstr, fromlist=[''])
            if call_with_mod:
                call_with_mod(module, app=app, pname=pname, package=package)
        except ImportError, e:
            raise_unexpected_import_error(impstr, e)

def gatherobjs(dotpath, filter, reloadmod=False):
    """
        like visitmods(), but instead of just importing the module it gathers
        objects out of the module, passing them to filter to determine if they
        should be kept or not.
    """
    def getkey(app, pname):
        if not pname:
            return 'appstack.%s' % dotpath
        return 'compstack.%s.%s' % (pname, dotpath)
    collected = OrderedDict()
    def process_module(module, app, pname, package):
        modkey = getkey(app, pname)
        for k, v in vars(module).iteritems():
            if filter(k, v):
                modattrs = collected.setdefault(modkey, OrderedDict())
                modattrs.setdefault(k, v)
    visitmods(dotpath, call_with_mod=process_module, reloadmod=reloadmod)
    return collected

class FileFinderBase(object):

    def __init__(self, pathpart):
        self.pathpart = ospath.normpath(pathpart)
        self.assign_cachekey()

    def cached_path(self):
        fullpath = ag.hierarchy_file_cache.get(self.cachekey)
        if fullpath:
            log.debug('found %s in cache: %s', self.cachekey, fullpath)
            return fullpath

    @classmethod
    def findfile(cls, endpoint_path):
        if ':' not in endpoint_path:
            return AppFileFinder(endpoint_path).search()
        component, pathpart = endpoint_path.split(':')
        return ComponentFileFinder(component, pathpart).search()

    def package_dir(self, package):
        package_mod = hm.builtin_import(package, fromlist=[''])
        return ospath.dirname(package_mod.__file__)

    def search(self):
        fullpath = self.cached_path()
        if fullpath:
            return fullpath

        fullpath = self.search_apps()
        if fullpath:
            ag.hierarchy_file_cache[self.cachekey] = fullpath
            return fullpath

class AppFileFinder(FileFinderBase):

    def assign_cachekey(self):
        self.cachekey = self.pathpart

    def search_apps(self):
        for app in listapps():
            testpath = ospath.join(self.package_dir(app), self.pathpart)
            if ospath.exists(testpath):
                return testpath

class ComponentFileFinder(FileFinderBase):

    def assign_cachekey(self):
        self.cachekey = '%s:%s' % (self.component, self.pathpart)

    def __init__(self, component, pathpart):
        self.component = component
        FileFinderBase.__init__(self, pathpart)

    def search_apps(self):
        for app, pname, package in list_component_mappings(self.component):
            if not package:
                testpath = ospath.join(self.package_dir(app), 'components', self.component, self.pathpart)
            else:
                testpath = ospath.join(self.package_dir(package), self.pathpart)
            if ospath.exists(testpath):
                return testpath

class FinderBase(object):

    def __init__(self, location, attr):
        self.cachekey = None
        self.location = location
        self.attr = attr
        self.assign_cachekey()

    @property
    def exclocation(self):
        return self.location

    def cached_module(self):
        module_location = ag.hierarchy_import_cache.get(self.cachekey)
        if module_location:
            module = hm.builtin_import(module_location, globals(), locals(), [''])
            log.debug('found %s in cache: %s', self.cachekey, module)
            return module

    def search(self):
        if not self.attr:
            raise ValueError('search() should not be used with an empty attr')
        module = self._search()
        if module:
            if hasattr(module, self.attr):
                return getattr(module, self.attr)
            # this happens when the attribute has been requested previously
            # but wasn't found, and the module was cached
            raise HierarchyImportError('attribute "%s" not found; searched %s.%s' % (self.attr, self.type, self.exclocation))

        log.debug('search() failed; resubmitting with empty attr for better error message')
        # try again with the attribute set to none to see if this is a problem
        # finding the module or finding the attribute
        orig_attr = self.attr
        self.attr = None
        module = self._search()
        if not module:
            raise HierarchyImportError('module "%s" not found; searched %s' % (self.exclocation, self.type))
        raise HierarchyImportError('attribute "%s" not found; searched %s.%s' % (orig_attr, self.type, self.exclocation))

    def _search(self):
        module = self.cached_module()
        if not module:
            module = self.search_apps()
        return module

    def try_import(self, dlocation):
        try:
            foundmod = hm.builtin_import(dlocation, globals(), locals(), [''])
            if self.attr is None or hasattr(foundmod, self.attr):
                log.debug('found %s: %s', self.cachekey, dlocation)
                ag.hierarchy_import_cache[self.cachekey] = dlocation
                return foundmod
        except ImportError, e:
            msg = str(e)
            if 'No module named ' in msg:
                not_found_mod = msg.replace('No module named ', '')
                if dlocation.endswith(not_found_mod):
                    return
            if dlocation in str(e):
                return
            raise

        log.debug('could not import: %s', self.cachekey)

class AppFinder(FinderBase):
    type = 'appstack'

    def assign_cachekey(self):
        self.cachekey = 'aopstack.%s:%s' % (self.location, self.attr)

    def search_apps(self):
        for app in listapps():
            dlocation = '%s.%s' % (app, self.location)
            module = self.try_import(dlocation)
            if module:
                return module

class ComponentFinder(FinderBase):
    type = 'compstack'

    def __init__(self, component, location, attr):
        self.component = component
        FinderBase.__init__(self, location, attr)

    @property
    def exclocation(self):
        return '%s.%s' % (self.component, self.location)

    def assign_cachekey(self):
        self.cachekey = 'compstack.%s.%s:%s' % (self.component, self.location, self.attr)

    def search_apps(self):
        for app, pname, package in list_component_mappings(self.component):
            if not package:
                dlocation = '%s.components.%s.%s' % (app, self.component, self.location)
            else:
                dlocation = '%s.%s' % (package, self.location)
            module = self.try_import(dlocation)
            if module:
                return module

class ImportOverrideHelper(object):

    def __init__(self, name, fromlist):
        self.name = name
        self.fromlist = fromlist

    @classmethod
    def doimport(cls, name, fromlist):
        if name.startswith('compstack.'):
            return CompstackImport(name, fromlist).search()
        if name.startswith('appstack.'):
            return AppstackImport(name, fromlist).search()

    def search(self):
        if not self.fromlist:
            raise HierarchyImportError('non-attribute importing is not supported; '
                              'use "from %s import foo, bar" syntax instead' % self.name)
        collector = BlankObject()
        for attr in self.fromlist:
            attrobj = self.find_attrobj(attr)
            setattr(collector, attr, attrobj)
        return collector


class CompstackImport(ImportOverrideHelper):
    type = 'compstack'

    def find_attrobj(self, attr):
        parts = self.name.split('.', 2)
        component = parts[1]
        try:
            name = parts[2]
        except IndexError:
            name = ''
        return ComponentFinder(component, name, attr).search()


class AppstackImport(ImportOverrideHelper):
    type = 'appstack'

    def find_attrobj(self, attr):
        _, name = self.name.split('.', 1)
        return AppFinder(name, attr).search()

def split_endpoint(endpoint):
    if ':' in endpoint:
        return endpoint.split(':')
    return None, endpoint
