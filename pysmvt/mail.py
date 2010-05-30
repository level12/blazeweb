"""
Tools for sending email.
"""

import logging
import mimetypes
import os
import smtplib
import socket
import time
import random
import re
from email import Charset, Encoders
from email.MIMEText import MIMEText
from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email.Header import Header
from email.Utils import formatdate, parseaddr, formataddr

from pysmvt import settings
from pysmvt.exceptions import SettingsError
from pysmvt.utils.encoding import smart_str, force_unicode
from pysmvt.utils import tolist, markdown
from html2text import html2text

log = logging.getLogger(__name__)

# Don't BASE64-encode UTF-8 messages so that we avoid unwanted attention from
# some spam filters.
Charset.add_charset('utf-8', Charset.SHORTEST, Charset.QP, 'utf-8')

# Default MIME type to use on attachments (if it is not explicitly given
# and cannot be guessed).
DEFAULT_ATTACHMENT_MIME_TYPE = 'application/octet-stream'

# Cache the hostname, but do it lazily: socket.getfqdn() can take a couple of
# seconds, which slows down the restart of the server.
class CachedDnsName(object):
    def __str__(self):
        return self.get_fqdn()

    def get_fqdn(self):
        if not hasattr(self, '_fqdn'):
            self._fqdn = socket.getfqdn()
        return self._fqdn

DNS_NAME = CachedDnsName()

# Copied from Python standard library, with the following modifications:
# * Used cached hostname for performance.
# * Added try/except to support lack of getpid() in Jython (#5496).
def make_msgid(idstring=None):
    """Returns a string suitable for RFC 2822 compliant Message-ID, e.g:

    <20020201195627.33539.96671@nightshade.la.mastaler.com>

    Optional idstring if given is a string used to strengthen the
    uniqueness of the message id.
    """
    timeval = time.time()
    utcdate = time.strftime('%Y%m%d%H%M%S', time.gmtime(timeval))
    try:
        pid = os.getpid()
    except AttributeError:
        # No getpid() in Jython, for example.
        pid = 1
    randint = random.randrange(100000)
    if idstring is None:
        idstring = ''
    else:
        idstring = '.' + idstring
    idhost = DNS_NAME
    msgid = '<%s.%s.%s%s@%s>' % (utcdate, pid, randint, idstring, idhost)
    return msgid

class BadHeaderError(ValueError):
    pass

def forbid_multi_line_headers(name, val):
    """Forbids multi-line headers, to prevent header injection."""
    val = force_unicode(val)
    if '\n' in val or '\r' in val:
        raise BadHeaderError("Header values can't contain newlines (got %r for header %r)" % (val, name))
    try:
        val = val.encode('ascii')
    except UnicodeEncodeError:
        if name.lower() in ('to', 'from', 'cc'):
            result = []
            for item in val.split(', '):
                nm, addr = parseaddr(item)
                nm = str(Header(nm, settings.default_charset))
                result.append(formataddr((nm, str(addr))))
            val = ', '.join(result)
        else:
            val = Header(val, settings.default_charset)
    else:
        if name.lower() == 'subject':
            val = Header(val)
    return name, val

class SafeMIMEText(MIMEText):
    def __setitem__(self, name, val):
        name, val = forbid_multi_line_headers(name, val)
        MIMEText.__setitem__(self, name, val)

class SafeMIMEMultipart(MIMEMultipart):
    def __setitem__(self, name, val):
        name, val = forbid_multi_line_headers(name, val)
        MIMEMultipart.__setitem__(self, name, val)

class SMTPConnection(object):
    """
    A wrapper that manages the SMTP network connection.
    """

    def __init__(self, host=None, port=None, username=None, password=None,
                 use_tls=None, fail_silently=False):
        self.host = host or settings.smtp.host
        self.port = port or settings.smtp.port
        self.username = username or settings.smtp.user
        self.password = password or settings.smtp.password
        self.use_tls = (use_tls is not None) and use_tls or settings.smtp.use_tls
        self.fail_silently = fail_silently
        self.connection = None

    def open(self):
        """
        Ensures we have a connection to the email server. Returns whether or
        not a new connection was required (True or False).
        """
        if self.connection:
            # Nothing to do if the connection is already open.
            return False
        try:
            # If local_hostname is not specified, socket.getfqdn() gets used.
            # For performance, we use the cached FQDN for local_hostname.
            self.connection = smtplib.SMTP(self.host, self.port,
                                           local_hostname=DNS_NAME.get_fqdn())
            if self.use_tls:
                self.connection.ehlo()
                self.connection.starttls()
                self.connection.ehlo()
            if self.username and self.password:
                self.connection.login(self.username, self.password)
            return True
        except:
            if not self.fail_silently:
                raise

    def close(self):
        """Closes the connection to the email server."""
        try:
            try:
                self.connection.quit()
            except socket.sslerror:
                # This happens when calling quit() on a TLS connection
                # sometimes.
                self.connection.close()
            except:
                if self.fail_silently:
                    return
                raise
        finally:
            self.connection = None

    def send_messages(self, email_messages):
        """
        Sends one or more EmailMessage objects and returns the number of email
        messages sent.
        """
        if not email_messages:
            return
        new_conn_created = self.open()
        if not self.connection:
            # We failed silently on open(). Trying to send would be pointless.
            return
        num_sent = 0
        for message in email_messages:
            sent = self._send(message)
            if sent:
                num_sent += 1
        if new_conn_created:
            self.close()
        return num_sent

    def _send(self, email_message):
        """A helper method that does the actual sending."""
        if not email_message.recipients():
            return False
        try:
            if settings.email.is_live:
                self.connection.sendmail(email_message.from_email,
                        email_message.recipients(),
                        email_message.message().as_string())
            else:
                log.warn('email.is_live = False, email getting skipped')
        except:
            if not self.fail_silently:
                raise
            return False
        return True

class EmailMessage(object):
    """
    A container for email information.
    """
    content_subtype = 'plain'
    multipart_subtype = 'mixed'
    encoding = None     # None => use settings default

    def __init__(self, subject='', body='', from_email=None, to=None, bcc=None,
            connection=None, attachments=None, headers=None, reply_to=None, cc=None):
        """
        Initialize a single email message (which can be sent to multiple
        recipients).

        All strings used to create the message can be unicode strings (or UTF-8
        bytestrings). The SafeMIMEText class will handle any necessary encoding
        conversions.
        """
        if to:
            assert not isinstance(to, basestring), '"to" argument must be a list or tuple'
            self.to = list(to)
        else:
            self.to = []
        if bcc:
            assert not isinstance(bcc, basestring), '"bcc" argument must be a list or tuple'
            self.bcc = list(bcc)
        else:
            self.bcc = settings.emails.bcc_defaults or []
        if cc:
            assert not isinstance(cc, basestring), '"cc" argument must be a list or tuple'
            self.cc = list(cc)
        else:
            self.cc = settings.emails.cc_defaults or []
        self.from_email = from_email or settings.emails.from_default
        self.reply_to = reply_to or settings.emails.reply_to
        self.subject = subject
        self.body = body
        self.attachments = attachments or []
        self.extra_headers = headers or {}
        self.connection = connection
        self._override_added = False
        self._always_recipients_added = False

    def get_connection(self, fail_silently=False):
        if not self.connection:
            self.connection = SMTPConnection(fail_silently=fail_silently)
        return self.connection

    def message(self):
        self._extend_recipients()
        self._perform_override()
        encoding = self.encoding or settings.default_charset
        msg = SafeMIMEText(smart_str(self.body, settings.default_charset),
                           self.content_subtype, encoding)
        if self.attachments:
            body_msg = msg
            msg = SafeMIMEMultipart(_subtype=self.multipart_subtype)
            if self.body:
                msg.attach(body_msg)
            for attachment in self.attachments:
                if isinstance(attachment, MIMEBase):
                    msg.attach(attachment)
                else:
                    msg.attach(self._create_attachment(*attachment))

        msg['Subject'] = self.subject
        if not self.from_email:
            raise SettingsError('email must have a from address or settings.emails.from_default must be set')
        msg['From'] = self.from_email
        if self.to:
            msg['To'] = ', '.join(self.to)
        if self.cc:
            msg['Cc'] = ', '.join(self.cc)
        
        # Email header names are case-insensitive (RFC 2045), so we have to
        # accommodate that when doing comparisons.
        header_names = [key.lower() for key in self.extra_headers]
        if 'date' not in header_names:
            msg['Date'] = formatdate()
        if 'message-id' not in header_names:
            msg['Message-ID'] = make_msgid()
        if self.reply_to:
            msg['Reply-To'] = self.reply_to
        
        for name, value in self.extra_headers.items():
            msg[name] = value
        return msg

    def recipients(self):
        """
        Returns a list of all recipients of the email (includes direct
        addressees, carbon copies, as well as Bcc entries).
        """
        self._extend_recipients()
        self._perform_override()
        return self.to + self.cc + self.bcc

    def send(self, fail_silently=False):
        """Sends the email message."""
        return self.get_connection(fail_silently).send_messages([self])

    def attach(self, filename=None, content=None, mimetype=None):
        """
        Attaches a file with the given filename and content. The filename can
        be omitted (useful for multipart/alternative messages) and the mimetype
        is guessed, if not provided.

        If the first parameter is a MIMEBase subclass it is inserted directly
        into the resulting message attachments.
        """
        if isinstance(filename, MIMEBase):
            assert content == mimetype == None
            self.attachments.append(filename)
        else:
            assert content is not None
            self.attachments.append([filename, content, mimetype])

    def attach_file(self, path, mimetype=None):
        """Attaches a file from the filesystem."""
        filename = os.path.basename(path)
        content = open(path, 'rb').read()
        self.attach(filename, content, mimetype)
    
    def _perform_override(self):
        if not self._override_added and settings.emails.override:
            self._override_added = True
            body_prepend = '%s\n\nTo: %s  \nCc: %s  \nBcc: %s\n\n%s\n\n' % (
                '-'*70,
                ', '.join(self.to),
                ', '.join(self.cc),
                ', '.join(self.bcc),
                '-'*70
            )
            self.to = tolist(settings.emails.override)
            self.cc = []
            self.bcc = []
            if self.content_subtype == 'html':
                body_prepend = markdown(body_prepend)
                self.body = self._insert_after_html_body(body_prepend, self.body)
            else:
                self.body = body_prepend + self.body
            
            # take care of any text/html alternative types
            for attachment in self.attachments:
                filename, content, mimetype = attachment
                if not filename and content and mimetype == 'text/html':
                    attachment[1] = self._insert_after_html_body(markdown(body_prepend), content)

    def _extend_recipients(self):
        """
        Adds the bcc_always and cc_always recipients to the lists
        if they are specified in the app settings.
        """
        if not self._always_recipients_added:
            if settings.emails.bcc_always:
                bcc_always = settings.emails.bcc_always
                if isinstance(bcc_always, str):
                    bcc_always = [bcc_always]
                self.bcc.extend(bcc_always)
            if settings.emails.cc_always:
                cc_always = settings.emails.cc_always
                if isinstance(cc_always, str):
                    cc_always = [cc_always]
                self.cc.extend(cc_always)
            self._always_recipients_added = True    

    def _create_attachment(self, filename, content, mimetype=None):
        """
        Converts the filename, content, mimetype triple into a MIME attachment
        object.
        """
        if mimetype is None:
            mimetype, _ = mimetypes.guess_type(filename)
            if mimetype is None:
                mimetype = DEFAULT_ATTACHMENT_MIME_TYPE
        basetype, subtype = mimetype.split('/', 1)
        if basetype == 'text':
            attachment = SafeMIMEText(smart_str(content,
                settings.default_charset), subtype, settings.default_charset)
        else:
            # Encode non-text attachments with base64.
            attachment = MIMEBase(basetype, subtype)
            attachment.set_payload(content)
            Encoders.encode_base64(attachment)
        if filename:
            attachment.add_header('Content-Disposition', 'attachment',
                                  filename=filename)
        return attachment

    def _insert_after_html_body(self, content, html):
        """
            will insert content in html after <body> or at the front if <body>
            isn't found
        """
        retval = re.sub('(<body.*?>)', r'\1%s' % content, html)
        if len(retval) == len(html):
            return content + html
        return retval
    
class EmailMultiAlternatives(EmailMessage):
    """
    A version of EmailMessage that makes it easy to send multipart/alternative
    messages. For example, including text and HTML versions of the text is
    made easier.
    """
    multipart_subtype = 'alternative'

    def attach_alternative(self, content, mimetype=None):
        """Attach an alternative content representation."""
        self.attach(content=content, mimetype=mimetype)

class MarkdownMessage(EmailMultiAlternatives):
    """
        Used the same way as EmailMessage, but the body is assumed to be
        Markdown formatted, which is converted to HTML using Markdown and then
        automatically attached as an alternative "text/html" content type.
    """
    def __init__(self, subject='', body='', from_email=None, to=None, bcc=None,
            connection=None, attachments=None, headers=None, reply_to=None, cc=None):
        EmailMultiAlternatives.__init__(self, subject, body, from_email, to, bcc,
            connection, attachments, headers, reply_to, cc)
        
        html_content = markdown(body)
        self.attach_alternative(html_content, "text/html")

class HtmlMessage(EmailMultiAlternatives):
    """
        Used the same way as EmailMessage, but the body is assumed to be
        HTML formatted, which is automatically attached as an alternative
        "text/html" content type, and also converted to Markdown formatted text
        for the main body.
    """
    def __init__(self, subject='', body='', from_email=None, to=None, bcc=None,
            connection=None, attachments=None, headers=None, reply_to=None, cc=None):
        html_content = body
        body = html2text(body)
        EmailMultiAlternatives.__init__(self, subject, body, from_email, to, bcc,
            connection, attachments, headers, reply_to, cc)
        
        self.attach_alternative(html_content, "text/html")

def get_email_class(format=None):
    if format == 'markdown':
        return MarkdownMessage
    elif format == 'html':
        return HtmlMessage
    return EmailMessage

def send_mail(subject, message, recipient_list, from_email=None, format='text',
              fail_silently=False, auth_user=None, auth_password=None):
    """
    Easy wrapper for sending a single message to a recipient list. All members
    of the recipient list will see the other recipients in the 'To' field.

    If auth_user is None, the EMAIL_HOST_USER setting is used.
    If auth_password is None, the EMAIL_HOST_PASSWORD setting is used.
    """
    connection = SMTPConnection(username=auth_user, password=auth_password,
                                fail_silently=fail_silently)
    email_class = get_email_class(format)
    return email_class(subject, message, from_email, recipient_list,
                        connection=connection).send()

def send_mass_mail(datatuple, format='text', fail_silently=False, auth_user=None,
                   auth_password=None):
    """
    Given a datatuple of (subject, message, from_email, recipient_list), sends
    each message to each recipient list. Returns the number of e-mails sent.

    If from_email is None, the emails.from_default setting is used.
    If auth_user and auth_password are set, they're used to log in.
    If auth_user is None, the EMAIL_HOST_USER setting is used.
    If auth_password is None, the EMAIL_HOST_PASSWORD setting is used.

    Note: The API for this method is frozen. New code wanting to extend the
    functionality should use the EmailMessage class directly.
    """
    connection = SMTPConnection(username=auth_user, password=auth_password,
                                fail_silently=fail_silently)
    email_class = get_email_class(format)
    messages = [email_class(subject, message, sender, recipient)
                for subject, message, sender, recipient in datatuple]
    return connection.send_messages(messages)

def _mail_admins(subject, message, format='text'):
    """used for testing"""
    email_class = get_email_class(format)
    fromaddr = settings.emails.from_server or settings.emails.from_default
    return email_class(settings.email.subject_prefix + subject, message,
                 fromaddr, settings.emails.admins
            )

def mail_admins(subject, message, format='text', fail_silently=False):
    """Sends a message to the programmers, as defined by the emails.programmers setting."""
    return _mail_admins(subject, message, format).send(fail_silently=fail_silently)
    

def _mail_programmers(subject, message, format='text'):
    """used for testing"""
    email_class = get_email_class(format)
    fromaddr = settings.emails.from_server or settings.emails.from_default
    return email_class(settings.email.subject_prefix + subject, message,
               fromaddr , settings.emails.programmers
            )

def mail_programmers(subject, message, format='text', fail_silently=False):
    """Sends a message to the programmers, as defined by the emails.programmers setting."""
    return _mail_programmers(subject, message, format).send(fail_silently=fail_silently)
    