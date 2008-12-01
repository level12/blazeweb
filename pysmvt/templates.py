# -*- coding: utf-8 -*-
from os import path
from pysmvt import ag, settings, appfilepath
from pysmvt.exceptions import ProgrammingError
from pysmvt.utils import safe_strftime
from jinja2 import FileSystemLoader, Environment, TemplateNotFound
from jinja2.loaders import split_template_path

class JinjaBase(object):
    
    def __init__(self, endpoint):
        
        # setup some needed attributes.  We have to do this at runtime instead
        # of putting them as class attributes b/c the class atrributes are
        # shared among instantiated classes
        self.templateName = None
        self.tpl_extension = None
        self._templateValues = {}

        app_mod_name = endpoint.split(':')[0]
                
        # change jinja tag style
        self.setOptions()
        
        # Setup Jinja template environment only once per process
        if hasattr(ag, 'templateEnv'):
            self.jinjaTemplateEnv = ag.templateEnv
        else:
            ag.jinjaTemplateEnv = self.templateEnv = Environment(**self._jinjaEnvOptions)
            ag.jinjaTemplateEnv.filters['strftime'] = safe_strftime
        
        # setup the AppTemplateLoader for each view that uses a template
        self.templateEnv.loader = AppTemplateLoader(app_mod_name)
        
    def setOptions(self):
        #jinja stuff has to be setup before we call parent init
        self._jinjaEnvOptions = {
                'block_start_string' : '<%',
                'block_end_string' : '%>',
                'variable_start_string' : '<{',
                'variable_end_string' : '}>',
                'comment_start_string' : '<#',
                'comment_end_string' : '#>',
            }
    
    def render(self):
        template = self.templateEnv.get_template(self.templateName + '.' + self.tpl_extension)
        return template.render(self._templateValues)
    
    def assign(self, key, value):
        self._templateValues[key] = value

class JinjaHtmlBase(JinjaBase):

    def __init__(self, modulePath):

        # call parent init
        JinjaBase.__init__(self, modulePath)
        
        #setup my own initilization values
        self.tpl_extension = 'html'

class AppTemplateLoader(FileSystemLoader):
    """
        A modification of Jinja's FileSystemLoader to take into account how
        pysmvt apps can inherit from other apps
    """

    def __init__(self, modname, encoding='utf-8'):
        self.encoding = encoding
        self.modname = modname

    def get_source(self, environment, template):
        pieces = split_template_path(template)
        modppath = path.join('modules', self.modname, 'templates', *pieces)
        apppath = path.join('templates', *pieces)
        try:
            fpath = appfilepath(modppath, apppath)
        except ProgrammingError, e:
            if 'could not locate' in str(e):
                raise TemplateNotFound(template)
            raise
        f = file(fpath)
        try:
            contents = f.read().decode(self.encoding)
        finally:
            f.close()
        old = path.getmtime(fpath)
        return contents, fpath, lambda: path.getmtime(fpath) == old
