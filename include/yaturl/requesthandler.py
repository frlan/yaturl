#!/usr/bin/env python
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
import time
from smtplib import SMTP, SMTPException
from email.mime.text import MIMEText
from urlparse import urlsplit, urlunsplit
from yaturl.db import YuDbError
from yaturl.constants import SERVER_NAME, SERVER_VERSION, TEMPLATE_500
from yaturl.helpers import sanitize_path, read_template


class YuRequestHandler(BaseHTTPRequestHandler):
    """
    Custom request handler to process HEAD, GET and POST requests
    """

    server_version = '%s/%s' % (SERVER_NAME, SERVER_VERSION)

    #----------------------------------------------------------------------
    def address_string(self):
        """
        Return the client address formatted for logging.
        Only lookup the hostname if really requested.
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
        """Send the response header and log the response code.

        Also send two standard headers with the server software
        version and the current date.
        """
        BaseHTTPRequestHandler.send_response(self, code, message)
        BaseHTTPRequestHandler.log_request(self, code, size)

    #----------------------------------------------------------------------
    def log_message(self, msg_format, *args):
        """
        Overwrite the default log_message() method which prints for
        some reason to stderr which we don't want.  Instead, we use a
        logger.
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
        try:
            self.send_response(301)
            self.send_header('Location', new_url)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
        except UnicodeEncodeError:
            self._send_internal_server_error()

    #----------------------------------------------------------------------
    def _send_404(self, header_only=False):
        text = read_template(
            self.server.config.get('templates','corruptlink'),
                title='yatURL.net - 404',
                header='404 &mdash Page not found',
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
        text = read_template(self.server.config.get('templates','servererror'),
            title='yatURL.net - Internal Error',
            header='Internal error')
        if not text:
            # fallback to hard-coded template
            text = TEMPLATE_500
        self._send_head(text, 500)
        if header_only == False:
            self.wfile.write(text)

    #----------------------------------------------------------------------
    def _send_database_problem(self, header_only=False):
        text = read_template(self.server.config.get('templates','databaseissuelink'),
            title='yatURL.net - Datebase error',
            header='Database error')
        if not text:
            self._send_internal_server_error()
            return
        self._send_head(text, 500)
        if header_only == False:
            self.wfile.write(text)

    #----------------------------------------------------------------------
    def _send_mail(self, subject, content, email):

        msg = MIMEText(content, 'plain', 'utf-8')

        msg['Subject'] = '%s' % (subject)
        msg['From'] = email
        msg['To'] = self.server.config.get('email','toemail')

        try:
            smtp_conn = SMTP('localhost')
            smtp_conn.sendmail(msg['From'], [msg['To']], msg.as_string())
            smtp_conn.quit()
        except SMTPException, e:
            self.server.errorlog('Mail could not be sent (%s)' % e)
            return False
        return True

    #----------------------------------------------------------------------
    def do_GET(self, header_only=False):
        # Homepage and other path ending with /
        # Needs to be extended later with things like FAQ etc.
        docroot = self.server.config.get('main', 'staticdocumentroot')
        local_path = sanitize_path(self.path)
        path =  docroot + local_path
        try:
            # actually try deliver the requested file - First we try to send
            # every static content
            requested_file = open(path)
            text = requested_file.read()
            requested_file.close()
        except IOError:
            if self.path == "/":
                text = read_template(
                    self.server.config.get('templates','statichomepage'),
                        title='yatURL.net',
                        header='yatURL.net',
                        msg='')
            elif self.path ==  '/URLRequest':
                # In case of there is a GET request to this page, just
                # return the homepage
                text = read_template(
                    self.server.config.get('templates','statichomepage'),
                    title='yatURL.net',
                    header='yatURL.net',
                    msg='')
            # Every other page
            else:
                # Assuming, if there is anything else than an alphanumeric
                # character after the starting /, it's not a valid hash at all
                if self.path[1:].isalnum():
                    try:
                        result = self.server.db.get_link_from_db(self.path[1:])
                    except YuDbError:
                        self._send_database_problem(header_only)
                        return
                    if result:
                        self._send_301(result[0])
                        return
                    else:
                        self._send_404(header_only)
                        return
                else:
                    self._send_404(header_only)
                    return

        if text:
            self._send_head(text, 200)
            self.end_headers()
            if header_only == False:
                self.wfile.write(text + "\n")
        else:
            self._send_internal_server_error(header_only)

    #----------------------------------------------------------------------
    def do_POST(self):
        form = cgi.FieldStorage(
                fp=self.rfile,
                headers=self.headers,
                environ={'REQUEST_METHOD':'POST'})
        if self.path == "/URLRequest":
            # TODO: Check for valid URL and avoid SQL injection later
            # inside this function

            # Doing some basic checks for submitted URL.  We assume,
            # if inside the inserted URL our domain name is included
            # its most likely an attempt to build up a circle which we
            # like to prevent from being established. If its not
            # intented to become a circle, well, its still something
            # unusual which we might don't want to have.

            if ('URL' in form and
                len(form['URL'].value) < 4096 and
                not form['URL'].value.find("yaturl.net") > -1):

                url = form['URL'].value

                # Now check, whether some protocol prefix is
                # available. If not, assume http:// was intended to put
                # there.

                if not url.find("://") > -1:
                    url = 'http://%s' % (url)
                url_split = urlsplit(url)
                # TODO rewrite this to something readable
                url_new = urlunsplit((url_split.scheme,
                          url_split.netloc.decode("utf-8 ").encode("idna"),
                          url_split.path, url_split.query,
                          url_split.fragment))

                link_hash = hashlib.sha1(url_new).hexdigest()

                # Begin the response
                try:
                    result = self.server.db.is_hash_in_db(link_hash)
                except YuDbError:
                    self._send_database_problem()
                    return
                if not result:
                    try:
                        short = self.server.db.add_link_to_db(link_hash, url_new)
                    except YuDbError:
                        self._send_database_problem()
                        return
                    new_url = '<a href="http://yaturl.net/%s">http://yaturl.net/%s</a>' % (short, short)
                    text = read_template(
                           self.server.config.get('templates','staticresultpage'),
                           title='yatURL.net &mdash; Result',
                           header='New URL',
                           URL=new_url)
                else:
                    # It appears link is already stored or you have found
                    # an collision on sha1
                    try:
                        short = self.server.db.get_short_for_hash_from_db(link_hash)[0]
                    except YuDbError:
                        self._send_database_problem()
                        return
                    new_url = '<a href="http://yaturl.net/%s">http://yaturl.net/%s</a>' % (short, short)
                    text = read_template(
                           self.server.config.get('templates','staticresultpage'),
                           title='yatURL.net - Short URL Result',
                           header='new URL',
                           URL=new_url)
            else:
                text = read_template(
                self.server.config.get('templates','statichomepage'),
                    title='yatURL.net',
                    header='yatURL.net',
                    msg="<p>Please check your input</p>")

        elif form and self.path == '/ContactUs':
            email = form['email'].value
            subj = form['subject'].value
            descr = form['request'].value
            if self._send_mail(subj, descr, email):
                text = read_template(
                    self.server.config.get('templates','contactUsResultpage'),
                    title='',
                    header='Mail sent',
                    msg="Your request has been sent. You will receive an answer soon.")
            else:
                self._send_internal_server_error()
                return
        else:
            self._send_404()

        if text:
            self._send_head(text, 200)
            self.wfile.write(text)
        else:
            self._send_internal_server_error()

    #----------------------------------------------------------------------
    def do_HEAD(self):
        """
        First attempt to implement HEAD response which is pretty much
        the same as the do_GET at the moment w/o sending the real
        data.... As so, we only need to call do_GET with parameter.
        """
        self.do_GET(True)
