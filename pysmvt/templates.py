# -*- coding: utf-8 -*-
from os import path
from pysmvt.application import request_context as rc
from pysmvt.utils import safe_strftime

class JinjaBase(object):
    
    def __init__(self, viewsModulePath):
        
        app = rc.application
        
        # setup some needed attributes.  We have to do this at runtime instead
        # of putting them as class attributes b/c the class atrributes are
        # shared among instantiated classes
        self.templateName = None
        self.templateExtension = None
        self._templateValues = {}
        
                
        # change jinja tag style
        self.setOptions()
        
        # Setup Jinja template environment only once per process
        try:
            self.jinjaTemplateEnv = app.templateEnv
        except AttributeError:
            from jinja2 import Environment
            app.jinjaTemplateEnv = self.templateEnv = Environment(**self._jinjaEnvOptions)
            app.jinjaTemplateEnv.filters['strftime'] = safe_strftime
        # setup the FileSystemLoader on each request
        from jinja2 import FileSystemLoader
        self.templateEnv.loader = FileSystemLoader([
                # templates in the module directory
                path.join(viewsModulePath, 'templates'),
                # tempaltes in the application directory
                path.join(app.baseDir, 'templates')
             ])
        
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
        template = self.templateEnv.get_template(self.templateName + '.' + self.templateExtension)
        return template.render(self._templateValues)
    
    def assign(self, key, value):
        self._templateValues[key] = value

class JinjaHtmlBase(JinjaBase):

    def __init__(self, modulePath):

        # call parent init
        JinjaBase.__init__(self, modulePath)
        
        #setup my own initilization values
        self.templateExtension = 'html'
        