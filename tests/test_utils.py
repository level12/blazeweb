from nose.tools import eq_
from paste.registry import StackedObjectProxy
from pysmvt.routing import current_url
from pysmvt.utils import wrapinapp, OrderedProperties, gather_objects, registry_has_object
from pysmvt import getview, rg
from pysmvt.test import create_request

# create the wsgi application that will be used for testing
from pysmvttestapp.applications import make_wsgi
app = make_wsgi('Testruns')

# call test_currenturl() inside of a working wsgi app.  current_url()
# depends on a correct environment being setup and would not work
# otherwise.
@wrapinapp(app)
def test_currenturl():
    assert current_url(host_only=True) == 'http://localhost/'
    
class TestWrapInApp(object):
    
    @wrapinapp(app)
    def test_currenturl(self):
        """ Works for class methods too """
        assert current_url(host_only=True) == 'http://localhost/'
    
    @wrapinapp(app)
    def test_getview(self):
        assert getview('tests:HwSnippet') == 'Hello World!'    
    
    @wrapinapp(app)
    def test_getview_with_css(self):
        assert getview('tests:HtmlSnippetWithCss') == 'no css'

def test_ordered_properties():
    class Opt(OrderedProperties):
        def __init__(self):
            self.from_init = 1
            OrderedProperties.__init__(self)
    
    o = Opt()
    o.after_init = 2
    
    assert o.from_init == 1
    assert o.__dict__['from_init'] == 1
    assert o.after_init == 2
    assert o._data['after_init'] == 2
    
    del o.from_init
    del o.after_init
    
    assert not hasattr(o, 'from_init')
    assert not hasattr(o, 'after_init')
    
    try:
        del o.not_there
        assert False, 'expected attribute error'
    except AttributeError:
        pass

class TestGatherObjects(object):
    
    @classmethod
    def setup_class(cls):
       cls.modlist = gather_objects('tasks.init_db')
    
    def test_correct_location(self):
        for modobjs in self.modlist:
            eq_(modobjs['loc'], modobjs['__name__'])
    
    def test_order(self):
        eq_(self.modlist[0]['loc'], 'pysmvttestapp.tasks.init_db')
        eq_(self.modlist[0]['loctoo'], 'pysmvttestapp2.tasks.init_db')
        eq_(self.modlist[1]['loc'], 'pysmvttestapp.modules.tests.tasks.init_db')
        eq_(self.modlist[1]['loctoo'], 'pysmvttestapp2.modules.tests.tasks.init_db')
        eq_(self.modlist[2]['loc'], 'pysmvttestapp.modules.nomodel.tasks.init_db')
        eq_(self.modlist[3]['loc'], 'pysmvttestapp.modules.routingtests.tasks.init_db')

    def test_count(self):
        assert len(self.modlist) == 4

def test_paste_bug():
    """
        http://trac.pythonpaste.org/pythonpaste/ticket/408
    """
    testsop = StackedObjectProxy(name="testsop")
    try:
        assert not testsop._object_stack()
        assert False, 'paste _object_stack() bug fixed, removed workaround in registry_has_object()'
    except AttributeError, e:
        if "'thread._local' object has no attribute 'objects'" == str(e):
            pass

class TestRegistryHasObject(object):
    testsop = StackedObjectProxy(name="testsop")
    
    def test_registry(self):
        assert not registry_has_object(self.testsop)
        foo = ''
        self.testsop._push_object(foo)
        assert registry_has_object(self.testsop)
        self.testsop._pop_object()
        assert not registry_has_object(self.testsop)
    
    @wrapinapp(app)
    def test_registry_has_object_with_wrapinapp(self):
        assert registry_has_object(rg)

class TestCreateRequest(object):
    
    def test_no_current_req_object(self):
        req = create_request({'foo':'bar'})
        assert req.form['foo'] == 'bar'
    
    @wrapinapp(app)
    def test_in_app(self):
        first_req = rg.request
        sec_req = create_request({'foo':'bar'})
        assert rg.request is sec_req

    @wrapinapp(app)
    def test_in_app_no_replace(self):
        first_req = rg.request
        sec_req = create_request({'foo':'bar'}, bind_to_context=False)
        assert rg.request is first_req