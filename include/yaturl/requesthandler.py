# -*- coding: utf-8 -*-
#
# Author:  Enrico Tröger
#          Frank Lanitz <frank@frank.uvena.de>
# License: GPL v2 or later
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
# MA 02110-1301, USA.

from BaseHTTPServer import BaseHTTPRequestHandler
import socket
import cgi
import hashlib
import socket
import time
from smtplib import SMTP, SMTPException
from email.mime.text import MIMEText
from urlparse import urlsplit, urlunsplit
from yaturl.db import YuDbError, YuDb
from yaturl.constants import SERVER_NAME, SERVER_VERSION, TEMPLATE_500
from yaturl.helpers import sanitize_path, read_template


class YuRequestHandler(BaseHTTPRequestHandler):
    """
    Custom request handler to process HEAD, GET and POST requests
    """

    server_version = '%s/%s' % (SERVER_NAME, SERVER_VERSION)


    #----------------------------------------------------------------------
    def __init__(self, request, client_address, server):
        self._db = YuDb(server.config, server.errorlog)
        BaseHTTPRequestHandler.__init__(self, request, client_address, server)

    #----------------------------------------------------------------------
    def __del__(self):
        del self._db

    #----------------------------------------------------------------------
    def _get_config_value(self, section, key):
        """
        Convenience function to retrieve config settings

        | **param** section (str)
        | **param** key (str)
        | **return** value (str)
        """
        return self.server.config.get(section, key)

    #----------------------------------------------------------------------
    def _get_config_template(self, key):
        """
        Convenience function to retrieve a template filename from the config

        | **param** key (str)
        | **return** value (str)
        """
        return self._get_config_value('templates', key)

    #----------------------------------------------------------------------
    def address_string(self):
        """
        Return the client address formatted for logging.
        Only lookup the hostname if really requested.

        | **return** hostname (str)
        """
        host = self.client_address[0]
        if self.server.resolve_clients:
            return socket.getfqdn(host)
        else:
            return host

    #----------------------------------------------------------------------
    def log_request(self, code='-', size='-'):
        """
        Overwrite the default log_request() method to make it a no-op.
        We call the original method ourselves to pass also the response size.
        """
        pass

    #----------------------------------------------------------------------
    def send_response(self, code, message=None, size='-'):
        """
        Send the response header and log the response code.

        Also send two standard headers with the server software
        version and the current date.

        | **param** code (int)
        | **param** message (str)
        | **param** size (str)
        """
        BaseHTTPRequestHandler.send_response(self, code, message)
        BaseHTTPRequestHandler.log_request(self, code, size)

    #----------------------------------------------------------------------
    def log_message(self, msg_format, *args):
        """
        Overwrite the default log_message() method which prints for
        some reason to stderr which we don't want.  Instead, we use a
        logger.

        | **param** msg_format (str)
        | **return** args (seq of mixed)
        """
        try:
            useragent = self.headers['User-Agent']
        except KeyError:
            useragent = '-'
        try:
            referrer = self.headers['Referer']
        except KeyError:
            referrer = '-'

        values = dict(
            client=self.address_string(),
            identity='-',
            user='-',
            timestr=time.strftime('%d/%a/%Y:%H:%M:%S %z'),
            request=msg_format % args,
            referrer='"%s"' % referrer,
            useragent='"%s"' % useragent
        )
        msg_format = '%(client)s %(identity)s %(user)s [%(timestr)s] %(request)s %(referrer)s %(useragent)s'
        self.server.accesslog.info(msg_format % values)

    #----------------------------------------------------------------------
    def _send_head(self, text, code):
        """
        Send common headers

        | **param** text (str)
        | **param** code (int)
        """
        size = len(text)
        self.send_response(code, None, size)
        if self.path.endswith(".css"):
            self.send_header('Content-Type', 'text/css')
        elif self.path.endswith(".ico"):
            self.send_header('Content-Type', 'image/vnd.microsoft.icon')
        else:
            self.send_header('Content-Type', 'text/html')
        self.send_header("Content-Length", size)
        self.end_headers()

    #----------------------------------------------------------------------
    def _send_301(self, new_url):
        """
        Send HTTP status code 301

        | **param** new_url (str)
        """
        try:
            self.send_response(301)
            self.send_header('Location', new_url)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
        except UnicodeEncodeError:
            self._send_internal_server_error()

    #----------------------------------------------------------------------
    def _send_404(self, header_only=False):
        """
        Send HTTP status code 404

        | **param** header_only (bool)
        """
        template_filename = self._get_config_template('corruptlink')
        text = read_template(
                template_filename,
                title='%s - 404' % SERVER_NAME,
                header='404 &mdash; Page not found',
                URL="Nothing")
        if text:
            self._send_head(text, 404)
            if header_only == False:
                try:
                    self.wfile.write(text)
                except socket.error:
                    # clients like to stop reading after they got a 404
                    pass
        else:
            self._send_internal_server_error(header_only)

    #----------------------------------------------------------------------
    def _send_internal_server_error(self, header_only=False):
        """
        Send HTTP status code 500

        | **param** header_only (bool)
        """
        template_filename = self._get_config_template('servererror')
        text = read_template(
            template_filename,
            title='%s - Internal Error' % SERVER_NAME,
            header='Internal error')
        if not text:
            # fallback to hard-coded template
            text = TEMPLATE_500
        self._send_head(text, 500)
        if header_only == False:
            self.wfile.write(text)

    #----------------------------------------------------------------------
    def _send_database_problem(self, header_only=False):
        """
        Send HTTP status code 500 due to a database connection error

        | **param** header_only (bool)
        """
        template_filename = self._get_config_template('databaseissuelink')
        text = read_template(
            template_filename,
            title='%s - Datebase error' % SERVER_NAME,
            header='Database error')
        if not text:
            self._send_internal_server_error()
            return
        self._send_head(text, 500)
        if header_only == False:
            self.wfile.write(text)

    #----------------------------------------------------------------------
    def _send_mail(self, subject, content, email):
        """
        Send a mail

        | **param** subject (str)
        | **param** content (str)
        | **param** email (str)
        """
        msg = MIMEText(content, 'plain', 'utf-8')

        msg['Subject'] = '%s' % (subject)
        msg['From'] = email
        msg['To'] = self._get_config_value('email', 'toemail')

        try:
            smtp_conn = SMTP('localhost')
            smtp_conn.sendmail(msg['From'], [msg['To']], msg.as_string())
            smtp_conn.quit()
        except (socket.error, SMTPException), e:
            self.server.errorlog.warn('Mail could not be sent (%s)' % e)
            return False
        return True

    #----------------------------------------------------------------------
    def _split_url(self, url):
        """
        Split the URL, decode the Network location part and unsplit the URL again

        | **param** url (str)
        | **return url_splitted (str)
        """
        url_split = urlsplit(url)
        decoded_netloc = url_split.netloc.decode("utf-8 ").encode("idna")
        url_parts = (
            url_split.scheme,
            decoded_netloc,
            url_split.path,
            url_split.query,
            url_split.fragment)
        url_splitted = urlunsplit(url_parts)
        return url_splitted

    #----------------------------------------------------------------------
    def _get_hash(self, *args):
        log_hash = hashlib.sha1()
        for value in args:
            value = unicode(value).encode('utf-8', 'replace')
            log_hash.update(value)
        return log_hash.hexdigest()

    #----------------------------------------------------------------------
    def _insert_url_to_db(self, url=None):
        """
        This function is intented to do the part of inserting to database
        and fetching (if already available) short URL

        It will return
        - the short hash in case of everything worked well
        - None in case of there was general issue with the URL
        - -1 in case of there was an issue with the database.
        - -2 in case of the hash is already in database, but URL are
             differing (SHA collision)

        | **param** url (str)
        | **return** status (mixed)
        """
        if url and len(url) < 4096 and not self.server.hostname.lower() in url.lower():

            # Now check, whether some protocol prefix is
            # available. If not, assume http:// was intended to put
            # there.
            if not '://' in url:
                url = 'http://%s' % (url)

            url_new = self._split_url(url)

            link_hash = self._get_hash(url_new)

            # Begin the response
            try:
                result = self._db.is_hash_in_db(link_hash)
            except YuDbError:
                # self._send_database_problem()
                return -1
            if not result:
                try:
                    short = self._db.add_link_to_db(link_hash, url_new)
                except YuDbError:
                    # self._send_database_problem()
                    return -1
            else:
                # It appears link is already stored or you have found
                # a collision on sha1
                # Let's check for a collision
                try:
                    url = self._db.get_link_from_db_by_complete_hash(link_hash)

                    if url_new == url:
                    # OK. We already have the url in DB. Good.
                        short = self._db.get_short_for_hash_from_db(link_hash)
                    else:
                    # Bad. We found a collision
                    # TODO: This might could be done more elegant by using an exception.
                        return -2
                except YuDbError:
                    return -1
        else:
            # If there is an issue with the URL given, we want to send over a
            # clear status to caller
            return None

        return short

    #----------------------------------------------------------------------
    def do_GET(self, header_only=False):
        """
        GET HTTP request entry point

        | **param** header_only (bool)
        """
        # Homepage and other path ending with /
        # Needs to be extended later with things like FAQ etc.
        docroot = self._get_config_value('main', 'staticdocumentroot')
        local_path = sanitize_path(self.path)
        path = docroot + local_path
        try:
            # actually try deliver the requested file - First we try to send
            # every static content
            requested_file = open(path)
            text = requested_file.read()
            requested_file.close()
        except IOError:
            if self.path in ('/', '/URLRequest'):
                template_filename = self._get_config_template('statichomepage')
                text = read_template(
                        template_filename,
                        title=SERVER_NAME,
                        header=SERVER_NAME,
                        msg='')
            # Any other page
            else:
                # First check, whether we want to have a real redirect
                # or just an info
                request_path = self.path
                if self.path.startswith('/show/'):
                    request_path = self.path[5:]
                    show = True
                elif self.path.startswith('/s/'):
                    request_path = self.path[2:]
                    show = True
                else:
                    show = False
                # Assuming, if there is anything else than an
                # alphanumeric character after the starting /, it's
                # not a valid hash at all
                if request_path[1:].isalnum():
                    try:
                        result = self._db.get_link_from_db(request_path[1:])
                    except YuDbError:
                        self._send_database_problem(header_only)
                        return
                    if result:
                        if show == True:
                            template_filename = self._get_config_template('showpage')
                            new_url = '<a href="%(result)s">%(result)s</a>' % \
                                      {'result':result}
                            text = read_template(
                                        template_filename,
                                        title=SERVER_NAME,
                                        header=SERVER_NAME,
                                        msg=new_url)
                        else:
                            self._send_301(result)
                            return
                    else:
                        self._send_404(header_only)
                        return
                else:
                    self._send_404(header_only)
                    return

        if text:
            self._send_head(text, 200)
            if header_only == False:
                self.wfile.write(text + "\n")
        else:
            self._send_internal_server_error(header_only)

    #----------------------------------------------------------------------
    def do_POST(self):
        """
        POST HTTP request entry point
        """
        form = cgi.FieldStorage(
                fp=self.rfile,
                headers=self.headers,
                environ={'REQUEST_METHOD':'POST'})

        if self.path == "/URLRequest":
            if form.has_key('URL'):
                template_filename = self._get_config_template('statichomepage')
                text = read_template(
                    template_filename,
                    title=SERVER_NAME,
                    header=SERVER_NAME,
                    msg='<p class="warning">Please check your input</p>')
            else:
                url = form['real_URL'].value if form.has_key('real_URL') else None
                tmp = self._insert_url_to_db(url)
                if tmp:
                    if tmp < 0:
                        self._send_database_problem()
                        return
                    else:
                        template_filename = self._get_config_template('staticresultpage')
                        text = read_template(
                                template_filename,
                                title='%s - Short URL Result' % SERVER_NAME,
                                header='new URL',
                                path = tmp,
                                hostname = self.server.hostname)
                else:
                    # There was a general issue with URL
                    template_filename = self._get_config_template('statichomepage')
                    text = read_template(
                        template_filename,
                        title=SERVER_NAME,
                        header=SERVER_NAME,
                        msg='<p class="warning">Please check your input</p>')

        elif self.path == '/ContactUs':
            try:
                email = form['email'].value
                subj = form['subject'].value
                descr = form['request'].value
                if self._send_mail(subj, descr, email):
                    template_filename = self._get_config_template('contactUsResultpage')
                    text = read_template(
                        template_filename,
                        title='',
                        header='Mail sent',
                        msg="Your request has been sent. You will receive an answer soon.")
                else:
                    self._send_internal_server_error()
                    return
            except KeyError:
                template_filename = self._get_config_template('contactUsResultpage')
                text = read_template(
                    template_filename,
                    title='',
                    header='Mail sent',
                    msg='It appers you did not fill out all needed fields. <a href="/ContactUs">Please try again</a>.')
        elif self.path == '/Show':
            short_url = form['ShortURL'].value if form.has_key('ShortURL') else None
            if short_url != None and short_url.find("yaturl.net") > -1:
                tmp = short_url.rfind("/")
                if tmp > -1 and short_url != "":
                    tmp = tmp + 1
                    short_url = short_url[tmp:]
            if short_url != None and short_url.isalnum():
                try:
                    result = self._db.get_link_from_db(short_url)
                except YuDbError:
                    self._send_database_problem(header_only=False)
                    return
                template_filename = self._get_config_template('showpage')
                if result:
                    new_url = '<p><a href="%(result)s">%(result)s</a></p>' % \
                              {'result':result}
                else:
                    new_url = '<p class="warning">No URL found for this string. Please double check your\
                                <a href="/ShowURL">input and try again</a></p>'
                text = read_template(template_filename, title=SERVER_NAME,
                          header=SERVER_NAME, msg=new_url)
            else:
                self._send_404()
                return

        else:
            self._send_404()
            return

        try:
            self._send_head(text, 200)
            self.wfile.write(text)
        except UnboundLocalError:
            self._send_internal_server_error()

    #----------------------------------------------------------------------
    def do_HEAD(self):
        """
        First attempt to implement HEAD response which is pretty much
        the same as the do_GET at the moment w/o sending the real
        data.... As so, we only need to call do_GET with parameter.
        """
        self.do_GET(header_only=True)
