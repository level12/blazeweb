import __builtin__
import logging

from pysutils.helpers import tolist
from pysmvt import ag, settings

log = logging.getLogger(__name__)

class HierarchyManager(object):
    
    def __init__(self):
        self.builtin_import = __builtin__.__import__
        self.replace_builtin()
    
    def apps_list(self, reverse=False):
        if reverse:
            apps = list(settings.apps.keys())
            apps.reverse()
            apps.append(settings.appname)
            return apps
        return [settings.appname] + settings.apps.keys()
    
    def plugin_settings(self, app, pname):
        if settings.appname == app:
            return settings.plugins.get(pname)
        app_settings = settings.apps.get(app)
        return app_settings.plugins.get(pname)

    def replace_builtin(self):
        __builtin__.__import__ = self.pysmvt_import
        log.debug('HierarchyManager replaced __builtin__.__import__')
        
    def restore_builtin(self):
        __builtin__.__import__ = self.builtin_import
        log.debug('HierarchyManager restored __builtin__.__import__')
    
    def pysmvt_import(self, name, globals={}, locals={}, fromlist=[], level=-1):
        return self.builtin_import(name, globals, locals, fromlist, level)
    
    def find_view(self, target):
        plugin, attr = target.split(':')
        if plugin == 'appstack':
            viewobj = AppFinder('views', attr).search()
        else:
            viewobj = PluginFinder(plugin, 'views', attr).search()
        if viewobj:
            return viewobj
        raise ImportError('the view target did not map to a view object: %s' % target)
        
hm = HierarchyManager()

class FinderBase(object):
    
    def __init__(self, location, attr):
        self.cachekey = None
        self.location = location
        self.attr = attr
        self.assign_cachekey()
    
    def cached_module(self):
        module_location = ag.import_cache.get(self.cachekey)
        if module_location:
            module = hm.builtin_import(module_location, globals(), locals(), [''])
            log.debug('found %s in cache: %s', self.cachekey, module)
            return module
        
    def search(self):
        cached_module = self.cached_module()
        if cached_module:
            return cached_module
        
        module = None
        for app in hm.apps_list():
            module = self.search_in_app(app)
            if module:
                break
        if module:
            return getattr(module, self.attr)

    def try_import(self, dlocation):
        
        try:
            foundmod = hm.builtin_import(dlocation, globals(), locals(), [''])
            if self.attr is None or hasattr(foundmod, self.attr):
                log.debug('found %s: %s', self.cachekey, dlocation)
                ag.import_cache[self.cachekey] = dlocation
                return foundmod
        except ImportError, e:
            if dlocation not in str(e):
                raise
        
        log.debug('could not import: %s', self.cachekey)

class AppFinder(FinderBase):
    
    def assign_cachekey(self):
        self.cachekey = '%s:%s' % (self.location, self.attr)

    def search_in_app(self, app):
        dlocation = '%s.%s' % (app, self.location)
        module = self.try_import(dlocation)
        if module:
            return module

class PluginFinder(FinderBase):
    
    def __init__(self, plugin, location, attr):
        self.plugin = plugin
        FinderBase.__init__(self, location, attr)
    
    def assign_cachekey(self):
        self.cachekey = '%s.%s:%s' % (self.plugin, self.location, self.attr)

    def search_in_app(self, app):
        psettings = hm.plugin_settings(app, self.plugin)
        if not psettings or not psettings.enabled:
            log.debug('the plugin %s is not enabled' % self.plugin)
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