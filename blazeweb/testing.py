import os

from decorator import decorator
from nose.tools import make_decorator
from blazeutils.datastructures import BlankObject
from webhelpers.html import tools
from werkzeug import Client as WClient, BaseRequest, BaseResponse, \
    cached_property, create_environ, run_wsgi_app

from blazeweb.globals import ag, settings, rg
from blazeweb.application import ResponseContext, RequestManager
from blazeweb.middleware import minimal_wsgi_stack
from blazeweb.hierarchy import findobj
from blazeweb.scripting import load_current_app, UsageError
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

def mock_smtp(cancel_override=True):
    ''' A decorator that allows you to test emails that are sent during
        functional or unit testing by mocking SMTP lib objects with the
        MiniMock library and giving the test function the tracker object
        to do tests with.

        :param cancel_override: in testing, we often will have email_overrides
            set so that emails don't get sent out for real.  Since this function
            prevents live emails from being sent, we will most often want
            to cancel that setting for the duration of the test so that the
            email tested is exactly what would be sent out if the emails were
            live.
        :raises: :exc:`ImportError` if the MiniMock library is not installed

    Example use::

    @mock_smtp()
    def test_user_form(self, mm_tracker=None):
        add_new_user_which_sends_email_to_user(form_data)
        look_for = """Called smtp_connection.sendmail(
    '...',
    [u'%s'],
    'Content-Type:...To: %s...You have been added to our """ \
            """system of registered users...REQUIRED to change it...
Called smtp_connection.quit()""" % (form_data['email_address'], form_data['email_address'])
        assert mm_tracker.check(look_for), mm_tracker.diff(look_for)
        # make sure only one email is sent out.  Can't == b/c from address
        # will change, but length is ~837, so 1000 seems safe
        assert len(mm_tracker.dump()) <= 1000, len(mm_tracker.dump())

        @mock_smtp()
        def test_that_fails():
            assert mm_tracker.check('Called smtp_connection.sendmail(...%s...has been issu'
                        'ed to reset the password...' % user.email_address)

    Other tracker methods::
        mm_tracker.dump(): returns minimock usage captured so far
        mm_tracker.diff(): returns diff of expected output and actual output
        mm_tracker.clear(): clears the tracker of everything captured
    '''
    try:
        import minimock
    except ImportError:
        raise ImportError('use of the assert_email decorator requires the minimock library')
    import smtplib
    def decorate(func):
        def newfunc(*arg, **kw):
            try:
                override = None
                # setup the mock objects so we can test the email getting sent out
                tt = minimock.TraceTracker()
                smtplib.SMTP = minimock.Mock('smtplib.SMTP', tracker=None)
                smtplib.SMTP.mock_returns = minimock.Mock('smtp_connection', tracker=tt)
                if cancel_override:
                    override = settings.emails.override
                    settings.emails.override = None
                kw['mm_tracker'] = tt
                func(*arg, **kw)
            finally:
                minimock.restore()
                if cancel_override:
                    settings.emails.override = override
        newfunc = make_decorator(func)(newfunc)
        return newfunc
    return decorate

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
        if 'html' not in self.content_type and 'xml' not in self.content_type:
            raise AttributeError(
                "Not an HTML or XML response body (content-type: %s)"
                % self.content_type)
        try:
            from pyquery import PyQuery
        except ImportError:
            raise ImportError(
                "You must have PyQuery installed to use response.pyquery")
        d = PyQuery(self.body)
        return d

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
        func_retval = None
        def wrapping_wsgi_app(env, start_response):
            start_response('200 OK', [('Content-Type', 'text/html')])
            with RequestManager(ag.app, environ):
                with ResponseContext(None):
                    func_retval = f(*args, **kwargs)
            return ['']
        run_wsgi_app(minimal_wsgi_stack(wrapping_wsgi_app), environ)
        return func_retval
    return decorator(inner)
