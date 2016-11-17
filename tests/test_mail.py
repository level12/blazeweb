import unittest

import six

from blazeutils.helpers import diff
from blazeutils.testing import logging_handler

from blazeweb.globals import settings
from . import config
from blazeweb.mail import EmailMessage, BadHeaderError, EmailMultiAlternatives, \
    MarkdownMessage, HtmlMessage, send_mail, _mail_programmers, _mail_admins
from blazeweb.exceptions import SettingsError
from blazeweb.testing import mockmail

###
#   lookfor values when using @mockmail
###
look_for = {}
look_for['text'] = """
Called blazeweb.mail.EmailMessage(
    'test subject',
    'email content',
    None,
    ['test@example.com'],
    ...)
Called blazeweb.mail.EmailMessage.send()""".strip()

look_for['markdown'] = """
Called blazeweb.mail.MarkdownMessage(
    'test markdown email',
    '**important** email content',
    None,
    ['test@example.com'],
    ...)
Called blazeweb.mail.MarkdownMessage.send()""".strip()

look_for['html'] = """
Called blazeweb.mail.HtmlMessage(
    'test html email',
    '<strong>important</strong> email content',
    None,
    ['test@example.com'],
    ...)
Called blazeweb.mail.HtmlMessage.send()""".strip()

###
#   tests
###


class TestEmail(unittest.TestCase):
    def setUp(self):
        self.app = config.make_wsgi()

    def tearDown(self):
        self.app = None

    def test_normal_ascii(self):
        """Test normal ascii character case"""
        email = EmailMessage('Subject', 'Content', 'from@example.com', ['to@example.com'])
        message = email.message()

        assert message['Subject'].encode() == 'Subject'
        assert message.get_payload() == 'Content'
        assert message['From'] == 'from@example.com'
        assert message['To'] == 'to@example.com'
        assert email.recipients() == ['to@example.com']

    def test_multi_recip(self):
        email = EmailMessage('Subject', 'Content', 'from@example.com',
                             ['to@example.com', 'other@example.com'])
        message = email.message()

        assert message['Subject'].encode() == 'Subject'
        assert message.get_payload() == 'Content'
        assert message['From'] == 'from@example.com'
        assert message['To'] == 'to@example.com, other@example.com'
        assert email.recipients() == ['to@example.com', 'other@example.com']

    def test_header_inj_sub(self):
        email = EmailMessage('Subject\nInjection Test', 'Content', 'from@example.com',
                             ['to@example.com'])

        try:
            email.message()
        except BadHeaderError as e:
            assert 'Header values can\'t contain newlines' in str(e)
        else:
            self.fail("header injection allowed in subject")

    def test_header_inj_from(self):
        email = EmailMessage('From Injection Test', 'Content',
                             'from@example.com\nto:spam@example.com', ['to@example.com'])

        try:
            email.message()
        except BadHeaderError as e:
            assert 'Header values can\'t contain newlines' in str(e)
        else:
            self.fail("header injection allowed in from")

    def test_header_inj_reply_to(self):
        email = EmailMessage('From Injection Test', 'Content', 'from@example.com',
                             ['to@example.com'], reply_to='reply@example.com\nto:spam@example.com')

        try:
            email.message()
        except BadHeaderError as e:
            assert 'Header values can\'t contain newlines' in str(e)
        else:
            self.fail("header injection allowed in reply_to")

    def test_header_inj_custom(self):
        email = EmailMessage('From Injection Test', 'Content', 'from@example.com',
                             ['to@example.com'],
                             headers={'X-test': 'reply@example.com\nto:spam@example.com'})

        try:
            email.message()
        except BadHeaderError as e:
            assert 'Header values can\'t contain newlines' in str(e)
        else:
            self.fail("header injection allowed in custom header")

    # Python 3 processes long headers differently
    if six.PY2:
        def test_long_subj(self):
            # Test for space continuation character in long (ascii) subject headers (#7747)
            expected = 'Content-Type: text/plain; charset="utf-8"\nMIME-Version: 1.0\n' \
                'Content-Transfer-Encoding: quoted-printable\nSubject: Long subject lines ' \
                'that get wrapped should use a space continuation\n character to get ' \
                'expected behaviour in Outlook and Thunderbird\nFrom: from@example.com' \
                '\nTo: to@example.com'
            email = EmailMessage('Long subject lines that get wrapped should use a space '
                                 'continuation character to get expected behaviour in Outlook '
                                 'and Thunderbird', 'Content', 'from@example.com',
                                 ['to@example.com'])
            message = email.message()
            assert message.as_string().startswith(expected), message.as_string()

    def test_default_from(self):
        email = EmailMessage('Subject', 'Content', to=['to@example.com'])
        message = email.message()

        assert message['Subject'].encode() == 'Subject'
        assert message.get_payload() == 'Content'
        assert message['From'] == 'root@localhost'
        assert message['To'] == 'to@example.com'

    def test_extra_header(self):
        email = EmailMessage('Subject', 'Content', to=['to@example.com'],
                             headers={'Reply-To': 'replyto@example.com'})
        message = email.message()

        assert message['Subject'].encode() == 'Subject'
        assert message.get_payload() == 'Content'
        assert message['From'] == 'root@localhost'
        assert message['To'] == 'to@example.com'
        assert message['Reply-To'] == 'replyto@example.com'

    def test_reply_to(self):
        email = EmailMessage('Subject', 'Content', to=['to@example.com'],
                             reply_to='replyto@example.com')
        message = email.message()

        assert message['Subject'].encode() == 'Subject'
        assert message.get_payload() == 'Content'
        assert message['From'] == 'root@localhost'
        assert message['To'] == 'to@example.com'
        assert message['Reply-To'] == 'replyto@example.com'

    def test_reply_to_default(self):
        settings.emails.reply_to = 'replyto@example.com'
        email = EmailMessage('Subject', 'Content', to=['to@example.com'])
        message = email.message()

        assert message['Subject'].encode() == 'Subject'
        assert message.get_payload() == 'Content'
        assert message['From'] == 'root@localhost'
        assert message['To'] == 'to@example.com'
        assert message['Reply-To'] == 'replyto@example.com'

    def test_bcc(self):
        email = EmailMessage('Subject', 'Content', to=['to@example.com'],
                             bcc=['bcc1@example.com', 'bcc2@example.com'])
        message = email.message()

        assert message['Subject'].encode() == 'Subject'
        assert message.get_payload() == 'Content'
        assert message['From'] == 'root@localhost'
        assert message['To'] == 'to@example.com'
        assert email.recipients() == ['to@example.com', 'bcc1@example.com', 'bcc2@example.com']

    def test_bcc_defaults(self):
        settings.emails.bcc_defaults = ['bcc1@example.com', 'bcc2@example.com']
        email = EmailMessage('Subject', 'Content', to=['to@example.com'])
        message = email.message()

        assert message['Subject'].encode() == 'Subject'
        assert message.get_payload() == 'Content'
        assert message['From'] == 'root@localhost'
        assert message['To'] == 'to@example.com'
        assert email.recipients() == ['to@example.com', 'bcc1@example.com', 'bcc2@example.com']

        email = EmailMessage('Subject', 'Content', to=['to@example.com'], bcc=['bcc3@example.com'])
        message = email.message()

        assert message['Subject'].encode() == 'Subject'
        assert message.get_payload() == 'Content'
        assert message['From'] == 'root@localhost'
        assert message['To'] == 'to@example.com'
        assert email.recipients() == ['to@example.com', 'bcc3@example.com']

    def test_cc(self):
        email = EmailMessage('Subject', 'Content', to=['to@example.com'],
                             cc=['cc1@example.com', 'cc2@example.com'])
        message = email.message()

        assert message['Subject'].encode() == 'Subject'
        assert message.get_payload() == 'Content'
        assert message['From'] == 'root@localhost'
        assert message['To'] == 'to@example.com'
        assert message['Cc'] == 'cc1@example.com, cc2@example.com'
        assert email.recipients() == ['to@example.com', 'cc1@example.com', 'cc2@example.com']

    def test_cc_defaults(self):
        settings.emails.cc_defaults = ['cc1@example.com', 'cc2@example.com']
        email = EmailMessage('Subject', 'Content', to=['to@example.com'])
        message = email.message()

        assert message['Subject'].encode() == 'Subject'
        assert message.get_payload() == 'Content'
        assert message['From'] == 'root@localhost'
        assert message['To'] == 'to@example.com'
        assert message['Cc'] == 'cc1@example.com, cc2@example.com'
        assert email.recipients() == ['to@example.com', 'cc1@example.com', 'cc2@example.com']

        email = EmailMessage('Subject', 'Content', to=['to@example.com'], cc=['cc3@example.com'])
        message = email.message()

        assert message['Subject'].encode() == 'Subject'
        assert message.get_payload() == 'Content'
        assert message['From'] == 'root@localhost'
        assert message['To'] == 'to@example.com'
        assert message['Cc'] == 'cc3@example.com'
        assert email.recipients() == ['to@example.com', 'cc3@example.com']

    def test_bcc_always(self):
        settings.emails.bcc_always = ['bcc1@example.com', 'bcc2@example.com']
        email = EmailMessage('Subject', 'Content', to=['to@example.com'])

        assert email.recipients() == ['to@example.com', 'bcc1@example.com', 'bcc2@example.com']
        message = email.message()
        assert message['Subject'].encode() == 'Subject'
        assert message.get_payload() == 'Content'
        assert message['From'] == 'root@localhost'
        assert message['To'] == 'to@example.com'

        email = EmailMessage('Subject', 'Content', to=['to@example.com'], bcc=['bcc3@example.com'])

        assert email.recipients() == ['to@example.com', 'bcc3@example.com', 'bcc1@example.com',
                                      'bcc2@example.com']
        message = email.message()
        assert message['Subject'].encode() == 'Subject'
        assert message.get_payload() == 'Content'
        assert message['From'] == 'root@localhost'
        assert message['To'] == 'to@example.com'

    def test_cc_always(self):
        settings.emails.cc_always = ['cc1@example.com', 'cc2@example.com']
        email = EmailMessage('Subject', 'Content', to=['to@example.com'])

        assert email.recipients() == ['to@example.com', 'cc1@example.com', 'cc2@example.com']
        message = email.message()
        assert message['Subject'].encode() == 'Subject'
        assert message.get_payload() == 'Content'
        assert message['From'] == 'root@localhost'
        assert message['To'] == 'to@example.com'
        assert message['Cc'] == 'cc1@example.com, cc2@example.com'

        email = EmailMessage('Subject', 'Content', to=['to@example.com'], cc=['cc3@example.com'])

        assert email.recipients() == ['to@example.com', 'cc3@example.com', 'cc1@example.com',
                                      'cc2@example.com']
        message = email.message()
        assert message['Subject'].encode() == 'Subject'
        assert message.get_payload() == 'Content'
        assert message['From'] == 'root@localhost'
        assert message['To'] == 'to@example.com'
        assert message['Cc'] == 'cc3@example.com, cc1@example.com, cc2@example.com'

    def test_overrides(self, mm_tracker=None):
        """Test overrides"""

        settings.emails.override = 'override@example.com'
        email = EmailMessage('Subject', 'Content', 'from@example.com', ['to@example.com'],
                             cc=['cc@example.com'], bcc=['bcc@example.com'])
        message = email.message()

        assert message['Subject'].encode() == 'Subject'
        assert message['From'] == 'from@example.com'
        assert message['To'] == 'override@example.com'
        assert message['Cc'] is None
        assert email.recipients() == ['override@example.com']

        msg_string = message.as_string()
        assert '-' * 70 in msg_string
        assert '\n\nTo: to@example.com' in msg_string
        assert '\nCc: cc@example.com' in msg_string
        assert '\nBcc: bcc@example.com' in msg_string
        assert '\nContent' in msg_string

    def test_overrides_recipients_first(self):
        """
            Test overrides, but call recipients first just like the code does
            when sending an email
        """

        settings.emails.override = 'override@example.com'
        email = EmailMessage('Subject', 'Content', 'from@example.com', ['to@example.com'],
                             cc=['cc@example.com'], bcc=['bcc@example.com'])
        assert email.recipients() == ['override@example.com']

        message = email.message()
        assert message['Subject'].encode() == 'Subject'
        assert message['From'] == 'from@example.com'
        assert message['To'] == 'override@example.com'
        assert message['Cc'] is None

        msg_string = message.as_string()
        assert '-' * 70 in msg_string
        assert '\n\nTo: to@example.com' in msg_string
        assert '\nCc: cc@example.com' in msg_string
        assert '\nBcc: bcc@example.com' in msg_string
        assert '\nContent' in msg_string

    def test_multi_part(self):
        text_content = 'This is an important message.'
        email = EmailMultiAlternatives('Subject', text_content, 'from@example.com',
                                       ['to@example.com'], cc=['cc@example.com'],
                                       bcc=['bcc@example.com'])

        html_content = '<p>This is an <strong>important</strong> message.</p>'
        email.attach_alternative(html_content, "text/html")

        message = email.message()
        text_part = \
            r"""Content-Type: text/plain; charset="utf-8"
MIME-Version: 1.0
Content-Transfer-Encoding: quoted-printable

This is an important message."""
        html_part = \
            r"""Content-Type: text/html; charset="utf-8"
MIME-Version: 1.0
Content-Transfer-Encoding: quoted-printable

<p>This is an <strong>important</strong> message.</p>"""

        text_message = message.as_string()
        assert text_part in text_message
        assert html_part in text_message

    def test_markdown_email(self):
        text_content = 'This is an **important** message.'
        email = MarkdownMessage('Subject', text_content, 'from@example.com', ['to@example.com'],
                                cc=['cc@example.com'], bcc=['bcc@example.com'])

        message = email.message()
        text_part = \
            r"""Content-Type: text/plain; charset="utf-8"
MIME-Version: 1.0
Content-Transfer-Encoding: quoted-printable

This is an **important** message."""
        html_part = \
            r"""Content-Type: text/html; charset="utf-8"
MIME-Version: 1.0
Content-Transfer-Encoding: quoted-printable

<p>This is an <strong>important</strong> message.</p>
"""

        text_message = message.as_string()
        assert text_part in text_message
        assert html_part in text_message

    def test_html_email(self):
        body = '<p>This is an <strong>important</strong> message.</p>'
        email = HtmlMessage('Subject', body, 'from@example.com', ['to@example.com'],
                            cc=['cc@example.com'], bcc=['bcc@example.com'])

        message = email.message()
        text_part = \
            r"""Content-Type: text/plain; charset="utf-8"
MIME-Version: 1.0
Content-Transfer-Encoding: quoted-printable

This is an **important** message.
"""
        html_part = \
            r"""Content-Type: text/html; charset="utf-8"
MIME-Version: 1.0
Content-Transfer-Encoding: quoted-printable

<p>This is an <strong>important</strong> message.</p>
"""

        text_message = message.as_string()
        assert text_part in text_message
        assert html_part in text_message

    def test_html_overrides(self):
        """Test overrides with html content"""

        settings.emails.override = 'override@example.com'
        body = '<p>This is an <strong>important</strong> message.</p>'
        email = EmailMessage('Subject', body, 'from@example.com', ['to@example.com'],
                             cc=['cc@example.com'], bcc=['bcc@example.com'])
        email.content_subtype = "html"  # Main content is now text/html
        message = email.message()

        msg_body = '<hr />\n\n<p>To: to@example.com <br />\nCc: cc@example.com <br />\n' \
            'Bcc: bcc@example.com</p>\n\n<hr />\n<p>This is an <strong>important</strong> ' \
            'message.</p>'
        assert msg_body in message.as_string()
        assert 'text/html;' in message['Content-Type']

    def test_html_override_with_full_document(self):
        html_doc = r"""<!DOCTYPE html
     PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
    "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">
  <head>
    <title>Minimal XHTML 1.0 Document with W3C DTD</title>
  </head>
  <body>
    <p>This is a minimal <a href="http://www.w3.org/TR/xhtml1/">XHTML 1.0</a>
    document with a W3C url for the DTD.</p>
  </body>
</html>"""
        settings.emails.override = 'override@example.com'
        email = EmailMessage('Subject', html_doc, 'from@example.com', ['to@example.com'],
                             cc=['cc@example.com'], bcc=['bcc@example.com'])
        email.content_subtype = "html"  # Main content is now text/html
        message = email.message()

        msg_body = '<body><hr />\n\n<p>To: to@example.com <br />\nCc: cc@example.com <br />\n' \
            'Bcc: bcc@example.com</p>\n\n<hr />\n\n    <p>This is a minimal '
        assert msg_body in message.as_string()
        assert 'text/html;' in message['Content-Type']

    def test_multipart_html_override_with_full_document(self):
        html_doc = r"""<!DOCTYPE html
     PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
    "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">
  <head>
    <title>Minimal XHTML 1.0 Document with W3C DTD</title>
  </head>
  <body>
    <p>This is a minimal <a href="http://www.w3.org/TR/xhtml1/">XHTML 1.0</a>
    document with a W3C url for the DTD.</p>
  </body>
</html>"""
        settings.emails.override = 'override@example.com'
        email = HtmlMessage('Subject', html_doc, 'from@example.com', ['to@example.com'])
        message = email.message()

        text_part = \
            r"""Content-Type: text/plain; charset="utf-8"
MIME-Version: 1.0
Content-Transfer-Encoding: quoted-printable

----------------------------------------------------------------------

To: to@example.com  =

Cc:   =

Bcc: =


----------------------------------------------------------------------

This is a minimal [XHTML 1.0](http://www.w3.org/TR/xhtml1/) document with a
W3C url for the DTD.
"""
        text_part_py3 = \
            r"""Content-Type: text/plain; charset="utf-8"
MIME-Version: 1.0
Content-Transfer-Encoding: quoted-printable

----------------------------------------------------------------------

To: to@example.com =20
Cc:  =20
Bcc:=20

----------------------------------------------------------------------

This is a minimal [XHTML 1.0](http://www.w3.org/TR/xhtml1/) document with a
W3C url for the DTD.
"""
        html_part = \
            r"""</head>
  <body><hr />

<p>To: to@example.com <br />
Cc: <br />
Bcc: </p>

<hr />

    <p>This is a minimal"""

        text_message = message.as_string()
        assert text_part in text_message or text_part_py3 in text_message, \
            diff(text_part_py3, text_message)
        assert html_part in text_message

    def test_not_live(self, mm_tracker=None):
        settings.email.is_live = False
        lh = logging_handler('blazeweb.mail')
        send_mail('test text email', 'email content', ['test@example.com'])
        assert 'email.is_live = False' in lh.messages['warning'][0]
        lh.reset()

    def test_email_log_entry(self):
        settings.email.is_live = False
        lh = logging_handler('blazeweb.mail')
        send_mail('test text email', 'email content', ['test@example.com'])
        assert 'Email sent: "test text email" to "test@example.com"' \
            in lh.messages['info'][0], lh.messages['info']
        lh.reset()

    def test_email_log_entry_multiple_senders(self):
        settings.email.is_live = False
        lh = logging_handler('blazeweb.mail')
        to = ['test%s@example.com' % n for n in range(0, 12)]
        send_mail('test text email', 'email content', to)
        assert 'Email sent: "test text email" to "test0@example.com;test1@example.com;' \
            'test2@example.com;test3@example.com;test4@example.com;test5@example.com;' \
            'test6@example.com;test7@example.com;test8@example.com;test9@example.com;' \
            'test10@example.com;t"' in lh.messages['info'][0], lh.messages['info']
        lh.reset()

    @mockmail
    def test_mockmail(self, mm_tracker=None):
        send_mail('test subject', 'email content', ['test@example.com'])

        assert mm_tracker.check(look_for['text']), mm_tracker.diff(look_for['text'])
        mm_tracker.clear()

        send_mail('test markdown email', '**important** email content', ['test@example.com'],
                  format='markdown')
        assert mm_tracker.check(look_for['markdown']), mm_tracker.diff(look_for['markdown'])
        mm_tracker.clear()

        send_mail('test html email', '<strong>important</strong> email content',
                  ['test@example.com'], format='html')
        assert mm_tracker.check(look_for['html']), mm_tracker.diff(look_for['html'])

    def test_duplicate_headers(self):
        # Specifying dates or message-ids in the extra headers overrides the default
        # values (#9233).

        headers = {"date": "Fri, 09 Nov 2001 01:08:47 -0000", "Message-ID": "foo"}
        email = EmailMessage('subject', 'content', 'from@example.com', ['to@example.com'],
                             headers=headers)
        print(email.message().as_string())
        msg_str = email.message().as_string()
        # testing with asserts because the ordering of date and Message-ID headers is
        # not guaranteed
        assert 'Content-Type: text/plain; charset="utf-8"' in msg_str
        assert 'MIME-Version: 1.0' in msg_str
        assert 'Content-Transfer-Encoding: quoted-printable' in msg_str
        assert 'Subject: subject' in msg_str
        assert 'From: from@example.com' in msg_str
        assert 'To: to@example.com' in msg_str
        assert 'date: Fri, 09 Nov 2001 01:08:47 -0000' in msg_str
        assert 'Message-ID: foo' in msg_str
        assert '\n\ncontent' in msg_str

    def test_mail_programmers(self):
        settings.email.subject_prefix = '[webapp] '
        settings.emails.programmers = ('p1@example.com', 'p2@example.com')

        email = _mail_programmers('programmers email subject', '**email body**', 'markdown')
        msg = email.message()

        assert msg['Subject'] == '[webapp] programmers email subject'
        assert email.recipients() == ['p1@example.com', 'p2@example.com']
        assert '<p><strong>email body</strong></p>' in msg.as_string()

    def test_mail_programmers_wawrning(self):
        lh = logging_handler('blazeweb.mail')
        settings.emails.programmers = []

        _mail_programmers('programmers email subject', 'email body')
        assert 'mail_programmers() used but settings.emails.programmers is empty' in \
            lh.messages['warning'][0]
        lh.reset()

    def test_mail_admins(self):
        settings.email.subject_prefix = '[webapp] '
        settings.emails.admins = ('a1@example.com', 'a2@example.com')
        email = _mail_admins('admins email subject', '**email body**', 'markdown')
        msg = email.message()

        assert msg['Subject'] == '[webapp] admins email subject'
        assert email.recipients() == ['a1@example.com', 'a2@example.com']
        assert '<p><strong>email body</strong></p>' in msg.as_string()

    def test_mail_admins_wawrning(self):
        lh = logging_handler('blazeweb.mail')
        settings.emails.admins = []

        _mail_admins('admins email subject', 'email body')
        assert 'mail_admins() used but settings.emails.admins is empty' in lh.messages['warning'][0]
        lh.reset()

    def test_nofrom(self):
        settings.emails.from_default = ''
        email = EmailMessage('Subject', 'Content', to=['to@example.com'])

        try:
            email.message()
            self.fail('expected SettingsError since from was not set')
        except SettingsError as e:
            assert 'email must have a from address' in str(e)

    def test_adminfrom(self):
        email = _mail_admins('admins email subject', '**email body**', 'markdown')
        msg = email.message()
        assert msg['From'] == 'root@localhost'

        settings.emails.from_server = 'server@localhost'
        email = _mail_admins('admins email subject', '**email body**', 'markdown')
        msg = email.message()
        assert msg['From'] == 'server@localhost'

    def test_programmersfrom(self):
        email = _mail_programmers('programmers email subject', '**email body**', 'markdown')
        msg = email.message()
        assert msg['From'] == 'root@localhost'

        settings.emails.from_server = 'server@localhost'
        email = _mail_programmers('programmers email subject', '**email body**', 'markdown')
        msg = email.message()
        assert msg['From'] == 'server@localhost'

if __name__ == '__main__':
    unittest.main()
