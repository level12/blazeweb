import __builtin__
import logging

from pysutils.datastructures import BlankObject
from pysutils.helpers import tolist
from pysmvt import ag, settings

log = logging.getLogger(__name__)

class HierarchyManager(object):
    
    def __init__(self):
        self.builtin_import = __builtin__.__import__
        self.replace_builtin()
    
    def apps_list(self, reverse=False):
        if reverse:
            apps = list(settings.supporting_apps)
            apps.reverse()
            apps.append(settings.appname)
            return apps
        return [settings.appname] + settings.supporting_apps

    def replace_builtin(self):
        __builtin__.__import__ = self.pysmvt_import
        log.debug('HierarchyManager replaced __builtin__.__import__')
        
    def restore_builtin(self):
        __builtin__.__import__ = self.builtin_import
        log.debug('HierarchyManager restored __builtin__.__import__')
    
    def pysmvt_import(self, name, globals={}, locals={}, fromlist=[], level=-1):
        instack_collection = ImportOverrideHelper.doimport(name, fromlist)
        if instack_collection:
            return instack_collection
        return self.builtin_import(name, globals, locals, fromlist, level)
hm = HierarchyManager()

def findview(endpoint):
    """
        locate a view object in the hierarchy based on an endpoint
    """
    if ':' not in endpoint:
        return AppFinder('views', endpoint).search()
    plugin, attr = endpoint.split(':')
    return PluginFinder(plugin, 'views', attr).search()

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
        module_location = ag.import_cache.get(self.cachekey)
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
            raise ImportError('attribute "%s" not found; searched %s.%s' % (self.attr, self.type, self.exclocation))
        
        log.debug('search() failed; resubmitting with empty attr for better error message')
        # try again with the attribute set to none to see if this is a problem
        # finding the module or finding the attribute
        orig_attr = self.attr
        self.attr = None
        module = self._search()
        if not module:
            raise ImportError('module "%s" not found; searched %s' % (self.exclocation, self.type))
        raise ImportError('attribute "%s" not found; searched %s.%s' % (orig_attr, self.type, self.exclocation))

    def _search(self):
        module = self.cached_module()
        if not module:
            for app in hm.apps_list():    
                print app
                module = self.search_in_app(app)
                if module:
                    break
        return module

    def try_import(self, dlocation):
        try:
            foundmod = hm.builtin_import(dlocation, globals(), locals(), [''])
            if self.attr is None or hasattr(foundmod, self.attr):
                log.debug('found %s: %s', self.cachekey, dlocation)
                ag.import_cache[self.cachekey] = dlocation
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
        self.cachekey = '%s:%s' % (self.location, self.attr)

    def search_in_app(self, app):
        dlocation = '%s.%s' % (app, self.location)
        module = self.try_import(dlocation)
        if module:
            return module

class PluginFinder(FinderBase):
    type = 'plugstack'
    
    def __init__(self, plugin, location, attr):
        self.plugin = plugin
        FinderBase.__init__(self, location, attr)
    
    @property
    def exclocation(self):
        return '%s.%s' % (self.plugin, self.location)

    def assign_cachekey(self):
        self.cachekey = '%s.%s:%s' % (self.plugin, self.location, self.attr)

    def search_in_app(self, app):
        try:
            psettings = settings.plugins.get_dotted('%s.%s' % (app, self.plugin))
        except AttributeError:
            psettings = None
        if not psettings or not psettings.enabled:
            log.debug('the plugin %s is not enabled for app %s' % (self.plugin, app))
            return
        
        # look in the application's source directory for plugins first
        dlocation = '%s.plugins.%s.%s' % (app, self.plugin, self.location)
        module = self.try_import(dlocation)
        if module:
            return module
        
        # look in the application's external plugins
        packages = psettings.get('packages')
        for package in tolist(packages):
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
        if name.startswith('plugstack.'):
            return PlugstackImport(name, fromlist).search()
        if name.startswith('appstack.'):
            return AppstackImport(name, fromlist).search()
    
    def search(self):
        if not self.fromlist:
            raise ImportError('non-attribute importing is not supported; '
                              'use "from %s import foo, bar" syntax instead' % self.name)
        collector = BlankObject()
        for attr in self.fromlist:
            attrobj = self.find_attrobj(attr)
            setattr(collector, attr, attrobj)
        return collector
        

class PlugstackImport(ImportOverrideHelper):
    type = 'plugstack'
    
    def find_attrobj(self, attr):
        parts = self.name.split('.', 2)
        plugin = parts[1]
        try:
            name = parts[2]
        except IndexError:
            name = ''
        return PluginFinder(plugin, name, attr).search()
        

class AppstackImport(ImportOverrideHelper):
    type = 'appstack'
    
    def find_attrobj(self, attr):
        _, name = self.name.split('.', 1)
        return AppFinder(name, attr).search()
    