from os import path
from nose.tools import eq_
from pysmvt.tasks import run_tasks
from pysmvt import getview
from pysmvt import settings
from pysmvt.logs import clear_settings_handlers
import logging
from pysmvttestapp.settings import basedir

# create the wsgi application that will be used for testing
from pysmvttestapp.applications import make_wsgi

log_base_dir = path.join(basedir, 'writeable', 'logs')

class LogsBase(object):
    
    @classmethod
    def setup_class(cls):        
        # have to clear the log files 
        # do this before the app is instantiated or else the files will have
        # write locks
        app_fh = open( path.join(log_base_dir, 'application.log'), 'w')
        app_fh.close()
        error_fh = open( path.join(log_base_dir, 'errors.log'), 'w')
        error_fh.close()
        #create the app
        make_wsgi(cls.settings_name)

    def lines(self, fname):
        fh = open( path.join(log_base_dir, '%s.log' % fname), 'r')
        try:
            return fh.readlines()
        finally:
            fh.close()
            
class TestLogs(LogsBase):
    
    settings_name = 'Testruns'
    
    def last_line(self, fname):
        lines = self.lines(fname)
            
        last_line = lines.pop()
        return last_line.split(' - ')

    def test_error_log(self):
        app_lines = self.lines('application')
        
        log = logging.getLogger('test_error_log')
        log.error('error message')
        
        _, type, name, message = self.last_line('errors')
        
        eq_('test_error_log', name.strip())
        eq_('error message', message.strip())
        
        assert len(app_lines) == len(self.lines('application')), 'error log is writing to application file'
        
        
    def test_application_log(self):
        log = logging.getLogger('test_application_log')
        log.application('application message')
        
        _, name, message = self.last_line('application')
        
        eq_('test_application_log', name.strip())
        eq_('application message', message.strip())
        
    def test_warn_log(self):
        log = logging.getLogger('test_error_log')
        log.warn('warn message')
        
        _, type, name, message = self.last_line('errors')
        
        eq_('test_error_log', name.strip())
        eq_('warn message', message.strip())
        
class TestNoLogs(LogsBase):
    
    settings_name = 'NoLogs'
    
    def test_no_logs(self):
        log = logging.getLogger('test_application_no_log')
        log.application('test_no_logs')
        
        log = logging.getLogger('test_error_no_log')
        log.error('test_no_logs')
        
        app_lines = self.lines('application')
        assert len(app_lines) == 0, app_lines
        
        error_lines = self.lines('errors')
        assert len(error_lines) == 0, error_lines
        