# -*- coding: utf-8 -*-
from os import path
from pysmvt import ag, settings
from pysmvt.utils import safe_strftime
from jinja2 import FileSystemLoader, Environment

class JinjaBase(object):
    
    def __init__(self, viewsModulePath):
        
        # setup some needed attributes.  We have to do this at runtime instead
        # of putting them as class attributes b/c the class atrributes are
        # shared among instantiated classes
        self.templateName = None
        self.tpl_extension = None
        self._templateValues = {}
        
                
        # change jinja tag style
        self.setOptions()
        
        # Setup Jinja template environment only once per process
        if hasattr(ag, 'templateEnv'):
            self.jinjaTemplateEnv = ag.templateEnv
        else:
            ag.jinjaTemplateEnv = self.templateEnv = Environment(**self._jinjaEnvOptions)
            ag.jinjaTemplateEnv.filters['strftime'] = safe_strftime
        
        # create a hierarchy of template directories the file loader (below)
        # can look to find the template
        lookin_paths = [
                # templates in the AM's template directory
                path.join(viewsModulePath, 'templates'),
                # templates in the application directory
                path.join(settings.dirs.templates)
                ]
        # templates in the supporting applications
        for sapp in settings.supporting_apps:
            sapp_dir = path.dirname(__import__(sapp).__file__)
            lookin_paths.append(path.join(sapp_dir, 'templates'))

        # setup the FileSystemLoader for each view that uses a template
        self.templateEnv.loader = FileSystemLoader(lookin_paths)
        
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
        