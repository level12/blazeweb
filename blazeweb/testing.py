from __future__ import with_statement
import os
import smtplib

from decorator import decorator
from nose.tools import make_decorator
from blazeutils.datastructures import BlankObject
from webhelpers.html import tools
from werkzeug import Client as WClient, BaseRequest, BaseResponse, \
    cached_property, create_environ, run_wsgi_app

from blazeweb.application import ResponseContext, RequestManager
from blazeweb.globals import ag, settings, rg, user
import blazeweb.mail
from blazeweb.middleware import minimal_wsgi_stack
from blazeweb.hierarchy import findobj
from blazeweb.scripting import load_current_app, UsageError
from blazeweb.users import UserProxy
from blazeweb.views import View
from blazeweb.wrappers import Request

try:
    from webtest import TestApp as WTTestApp
    from webtest import TestResponse as WTTestResponse
except ImportError:
    WTTestApp = None

class Client(WClient):

    def open(self, *args, **kwargs):
        """
            if follow_redirects is requested, a (BaseRequest, response) tuple
            will be returned, the request being the last redirect request
            made to get the response
        """
        fr = kwargs.get('follow_redirects', False)
        if fr:
            kwargs['as_tuple'] = True
        retval = WClient.open(self, *args, **kwargs)
        if fr:
            return BaseRequest(retval[0]), retval[1]
        return retval

def mockmail(func):
    '''
        A decorator that allows you to test emails that are sent during
        functional or unit testing by mocking blazeweb.mail.EmailMessage and
        subclasses with the MiniMock library.

        The decorator should be used on test functions or methods that test
        email sending functionality.

        :raises: :exc:`ImportError` if the MiniMock library is not installed

    Example use::

    @mockmail
    def test_mockmail(self, mm_tracker=None):
        send_mail('test subject', 'email content', ['test@example.com'])
        look_for = """
Called blazeweb.mail.EmailMessage(
    'test subject',
    'email content',
    None,
    ['test@example.com'],
    ...)
Called blazeweb.mail.EmailMessage.send()""".strip()
        assert mm_tracker.check(look_for), mm_tracker.diff(look_for)
        mm_tracker.clear()

    Other tracker methods::
        mm_tracker.dump(): returns minimock usage captured so far
        mm_tracker.diff(): returns diff of expected output and actual output
        mm_tracker.clear(): clears the tracker of everything captured
    '''
    try:
        import minimock
    except ImportError:
        raise ImportError('use of the mockmail decorator requires the minimock library')
    def newfunc(*arg, **kw):
        try:
            override = None
            # setup the mock objects so we can test the email getting sent out
            tt = minimock.TraceTracker()
            minimock.mock('blazeweb.mail.EmailMessage', tracker=tt)
            blazeweb.mail.EmailMessage.mock_returns = minimock.Mock('blazeweb.mail.EmailMessage', tracker=tt)
            minimock.mock('blazeweb.mail.MarkdownMessage', tracker=tt)
            blazeweb.mail.MarkdownMessage.mock_returns = minimock.Mock('blazeweb.mail.MarkdownMessage', tracker=tt)
            minimock.mock('blazeweb.mail.HtmlMessage', tracker=tt)
            blazeweb.mail.HtmlMessage.mock_returns = minimock.Mock('blazeweb.mail.HtmlMessage', tracker=tt)
            kw['mm_tracker'] = tt
            func(*arg, **kw)
        finally:
            minimock.restore()
    return make_decorator(func)(newfunc)

class TestResponse(BaseResponse):

    @cached_property
    def fdata(self):
        return self.filter_data()

    @cached_property
    def wsdata(self):
        return self.filter_data(strip_links=False)

    def filter_data(self, normalize_ws=True, strip_links=True):
        data = super(TestResponse, self).data
        if normalize_ws:
            data = ' '.join(data.split())
        return data if not strip_links else tools.strip_links(data)

if WTTestApp:
    # we import TestApp from here to make sure TestResponse gets patched with
    # pyquery
    class TestApp(WTTestApp):
        pass

    def pyquery(self):
        """
        Returns the response as a `PyQuery <http://pyquery.org/>`_ object.

        Only works with HTML and XML responses; other content-types raise
        AttributeError.
        """
        if not hasattr(self, '__pyquery_d'):
            if 'html' not in self.content_type and 'xml' not in self.content_type:
                raise AttributeError(
                    "Not an HTML or XML response body (content-type: %s)"
                    % self.content_type)
            try:
                from pyquery import PyQuery
            except ImportError:
                raise ImportError(
                    "You must have PyQuery installed to use response.pyquery")
            self.__pyquery_d = PyQuery(self.body)
        return self.__pyquery_d

    WTTestResponse.pyq = property(pyquery, doc=pyquery.__doc__)
else:
    class TestApp(object):
        def __init__(self, *args, **kwargs):
            raise ImportError('You must have WebTest installed to use TestApp')

def inrequest(path='/[[@inrequest]]', *args, **kwargs):
    environ = create_environ(path, *args, **kwargs)
    def inner(f, *args, **kwargs):
        """
            This sets up request and response context for testing pursposes.
            The arguments correspond to Werkzeug.create_environ() arguments.
        """
        def wrapping_wsgi_app(env, start_response):
            start_response('200 OK', [('Content-Type', 'text/html')])
            with RequestManager(ag.app, environ):
                with ResponseContext(None):
                    func_retval = f(*args, **kwargs)
                    environ['pysmvt.testing.inrequest:func_retval'] = func_retval
            return ['']
        run_wsgi_app(minimal_wsgi_stack(wrapping_wsgi_app), environ)
        return environ['pysmvt.testing.inrequest:func_retval']
    return decorator(inner)

def runview(view, path='/[[@runview]]', *args, **kwargs):
    if not isinstance(view, View) and issubclass(view, View):
        # the view is a class, not an instance, so instantiate with empty
        # URL args and a fake endpoint
        view = view({}, '__testing__')
    funcretval = None
    req_pre = kwargs.pop('pre', None)
    req_post = kwargs.pop('post', None)
    required_status = kwargs.pop('status', 200)
    @inrequest(path, *args, **kwargs)
    def runview_inner():
        if req_pre is not None:
            req_pre()
        resp = view.process()
        # this is the same logic that is used in RequestManager.__exit__()
        # but we just attach directly to the response object instead of putting
        # it in the environ
        u = user._current_obj()
        if isinstance(u, UserProxy):
            # we don't want to send the UserProxy outside of the request
            # because we will get a StackedObjectProxy error when trying
            # to access it.  Better to just send None, b/c an attribute
            # error on None is easier to understand in testing than
            # a proxy registry error
            resp.user = None
        else:
            resp.user = u
        if req_post is not None:
            req_post()
        assert resp.status_code == required_status, 'unexpected status code: %s' % resp.status_code
        return resp
    return runview_inner()
