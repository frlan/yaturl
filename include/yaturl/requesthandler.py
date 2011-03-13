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
from urlparse import urlsplit, urlunsplit, urlparse
from yaturl.database.database import YuDatabase
from yaturl.database.error import YuDatabaseError
from yaturl.constants import SERVER_NAME, SERVER_VERSION, TEMPLATE_500, CONTENT_TYPES
from yaturl.helpers.path import sanitize_path
from yaturl.helpers.template import read_template
from yaturl.stats import YuStats, YuLinkStats


class YuRequestHandler(BaseHTTPRequestHandler):
    """
    Custom request handler to process HEAD, GET and POST requests
    """

    server_version = '%s/%s' % (SERVER_NAME, SERVER_VERSION)


    #----------------------------------------------------------------------
    def __init__(self, request, client_address, server):
        self._db = YuDatabase(server.config, server.errorlog)
        BaseHTTPRequestHandler.__init__(self, request, client_address, server)

    #----------------------------------------------------------------------
    def __del__(self):
        self._db.close()

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
        tmp_path = self._get_config_value('templates', 'path') + key
        return tmp_path

    #----------------------------------------------------------------------
    def address_string(self):
        """
        Return the client address formatted for logging.
        Only lookup the hostname if really requested.

        | **return** hostname (str)
        """

        if self.server.log_ip_activated:
            host = self.client_address[0]
        else:
            host = '127.0.0.1'
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
        # Trying to figure out what we are going to send out.
        # Maybe this could be improved a bit further but should do
        # it for now.
        extension_start = self.path.rfind('.')
        extension = self.path[extension_start:]
        try:
            self.send_header('Content-Type', CONTENT_TYPES[extension])
        except KeyError:
            self.send_header('Content-Type', 'text/html')
        self.send_header("Content-Length", size)
        self.end_headers()

    #-------------------------------------------------------------------
    def _send_response(self, content, code=200, header_only=False):
        """
        This function is to be intended to consolidate the
        sending responses to on function.
        TODO: Synch with self.send_response() function which is
              already talking with HTTPServer-interface.

        | **param** content - text of page (str)
        | **param** code - response code e.g. 404 (int)
        | **param** header_only - whether only headers should be send (bool)
        """
        if content:
            self._send_head(content, code)
            if header_only == False:
                try:
                    self.wfile.write(content)
                except socket.error:
                    # clients like to stop reading after they got a 404
                    pass
        else:
            self._send_internal_server_error(header_only)

    #-------------------------------------------------------------------
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
        template_filename = self._get_config_template('404')
        text = read_template(
                template_filename,
                title='%s - 404' % SERVER_NAME,
                header='404 &mdash; Page not found',
                URL="Nothing")
        self._send_response(text, 404, header_only)

    #----------------------------------------------------------------------
    def _send_internal_server_error(self, header_only=False):
        """
        Send HTTP status code 500

        | **param** header_only (bool)
        """
        template_filename = self._get_config_template('500')
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
        template_filename = self._get_config_template('databaserror')
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
        try:
            decoded_netloc = url_split.netloc.decode("utf-8 ").encode("idna")
            url_parts = (
                url_split.scheme,
                decoded_netloc,
                url_split.path,
                url_split.query,
                url_split.fragment)
            url_splitted = urlunsplit(url_parts)
            return url_splitted
        except UnicodeError:
            return None

    #----------------------------------------------------------------------
    def _get_hash(self, *args):
        """
        Wrapper function which returns the SHA-1-hash of given set of
        strings

        | **param** args -- set of strings (str)
        | **return** hash
        """
        url_hash = hashlib.sha1()
        try:
            for value in args:
                value = unicode(value).encode('utf-8', 'replace')
                url_hash.update(value)
            return url_hash.hexdigest()
        except UnicodeDecodeError:
            return None

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

            # Checking whether we were able to create an hash for that
            # URL to proceed further
            if not link_hash:
                return None

            # Begin the response
            try:
                result = self._db.is_hash_in_db(link_hash)
            except YuDatabaseError:
                # self._send_database_problem()
                return -1
            if not result:
                try:
                    short = self._db.add_link_to_db(link_hash, url_new)
                except YuDatabaseError:
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
                        self._send_mail('Collision on SHA found',
                            '%s vs %s' % (url_new, url), self._get_config_value('email', 'toemail'))
                        return -2
                except YuDatabaseError:
                    return -1
        else:
            # If there is an issue with the URL given, we want to send over a
            # clear status to caller
            return None

        return short

    #-------------------------------------------------------------------
    def _show_general_stats(self, header_only=False):
        """
        Prints a page with some serice wide statistics.

        | **param** header_only (bool)
        """

        stat = YuStats(self.server)
        template_filename = self._get_config_template('stats')
        text = read_template(
                    template_filename,
                    title=SERVER_NAME,
                    header=SERVER_NAME,
                    number_of_links=stat.links_all,
                    number_of_redirects=stat.redirect_all,
                    number_of_redirects_today = stat.redirect_today,
                    number_of_redirects_this_week = stat.redirect_this_week,
                    number_of_redirects_this_month = stat.redirect_this_month,
                    number_of_redirects_this_year = stat.redirect_this_year,
                    number_of_url_today = stat.links_today,
                    number_of_url_this_week = stat.links_this_week,
                    number_of_url_this_month = stat.links_this_month,
                    number_of_url_this_year = stat.links_this_year,
                    date_of_first_redirect = stat.date_of_first_redirect,
                )
        if text:
            self._send_head(text, 200)
            if header_only == False:
                try:
                    self.wfile.write(text)
                except socket.error:
                    # clients like to stop reading after they got a 404
                    pass
        else:
            self._send_internal_server_error(header_only)

    #-------------------------------------------------------------------
    def _show_link_stats(self, header_only=False, shorthash=None):
        """
        Shows a page with some statistics for a short URL

        | **param** shorthash (string)
        """

        # First doing some basis input validation as we don't want to
        # get fucked by the Jesus
        if shorthash == None or not shorthash.isalnum():
            self._send_404(header_only)
            return
        else:
            blocked = self._db.is_hash_blocked(shorthash)
            if blocked:
                template_filename = self._get_config_template('blocked')
                text = read_template(
                        template_filename,
                        title=SERVER_NAME,
                        header=SERVER_NAME,
                        comment=blocked[3])
                self._send_response(text, 200, header_only)

            link_stats = YuLinkStats(self.server, shorthash)
            # Only proceed if there is a address behind the link,
            # else sending a 404
            if link_stats.link_address:
                template_filename = self._get_config_template('statsLink')
                url = "/" + shorthash
                new_url = '<a href="%(url)s">%(result)s</a>' % \
                            {'result':link_stats.link_address, 'url':url}
                # FIXME: Check for None on timestamps and replace it with something like Unknown.
                text = read_template(
                        template_filename,
                        title='%s - Linkstats' % SERVER_NAME,
                        header='Stats for Link',
                        URL=new_url,
                        CREATION_TIME=link_stats.creation_time,
                        FIRST_REDIRECT=link_stats.first_redirect,
                        LAST_REDIRECT=link_stats.last_redirect,
                        NUMBER_OF_REDIRECTS=link_stats.number_of_redirects)
                self._send_response(text, 200, header_only)
            else:
                self._send_404(header_only)
                return

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
            try:
                parsed_path = urlparse(self.path)
                params = dict([p.split('=') for p in parsed_path[4].split('&')])
                if params['addurl']:
                    tmp = self._insert_url_to_db(params['addurl'])
                    if tmp and tmp < 0:
                        self._send_database_problem()
                        return
                    blocked = self._db.is_hash_blocked(tmp)
                    if blocked:
                        template_filename = self._get_config_template('blocked')
                        text = read_template(
                                    template_filename,
                                    title=SERVER_NAME,
                                    header=SERVER_NAME,
                                    comment=blocked[3])
                    elif tmp:
                        template_filename = self._get_config_template('return')
                        text = read_template(
                                template_filename,
                                title='%s - Short URL Result' % SERVER_NAME,
                                header='new URL',
                                path = tmp,
                                hostname = self.server.hostname)
                    else:
                        # There was a general issue with URL
                        template_filename = self._get_config_template('homepage')
                        text = read_template(
                            template_filename,
                            title=SERVER_NAME,
                            header=SERVER_NAME,
                            msg='''<p class="warning">Please check your input.</p>''')
            except YuDatabaseError:
                self._send_database_problem(header_only)
                return
            except:
                if self.path in ('/', '/URLRequest'):
                    template_filename = self._get_config_template('homepage')
                    text = read_template(
                            template_filename,
                            title=SERVER_NAME,
                            header=SERVER_NAME,
                            msg='')
                elif self.path.startswith('/stats') or self.path.endswith('+'):
                    if self.path == '/stats':
                        # Doing general statistics here
                        # Let's hope this page is not getting to popular ....
                        # Create a new stats objekt which is fetching data in background
                        self._show_general_stats(header_only)
                        return
                    else:
                        # Check whether we do have the + or the stats kind of URL
                        if self.path.endswith('+'):
                            # Well I guess this is the proof you can write
                            # real ugly code in Python too.
                            try:
                                if self.path.startswith('/show/'):
                                    request_path = self.path[6:]
                                elif self.path.startswith('/s/'):
                                    request_path = self.path[3:]
                                elif self.path.startswith('/stats/'):
                                    request_path = self.path[7:]
                                else:
                                    request_path = self.path[1:]
                                self._show_link_stats(header_only,
                                    request_path[:request_path.rfind('+') ])
                                return
                            except:
                                # Oopps. Something went wrong. Most likely
                                # a malformed link
                                self._send_404()
                                return
                        else:
                            # Trying to understand for which link we shall print
                            # out stats.
                            splitted = self.path[1:].split('/')
                            try:
                                self._show_link_stats(header_only, splitted[1])
                                return
                            except IndexError:
                                # Something went wrong. Most likely there was a
                                # malformed URL for accessing the stats.
                                self._send_404()
                                return
                elif self.path == '/faq':
                    template_filename = self._get_config_template('faq')
                    text = read_template(
                            template_filename,
                            title=SERVER_NAME,
                            header=SERVER_NAME,)
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
                            blocked = self._db.is_hash_blocked(request_path[1:])
                        except YuDatabaseError:
                            self._send_database_problem(header_only)
                            return
                        if result and blocked == None:
                            if show == True:
                                template_filename = self._get_config_template('showpage')
                                url = "/" + request_path[1:]
                                new_url = '<p><a href="%(url)s">%(result)s</a></p>' % \
                                          {'result':result, 'url':url}
                                stats = self._db.get_statistics_for_hash(request_path[1:])
                                text = read_template(
                                            template_filename,
                                            title=SERVER_NAME,
                                            header=SERVER_NAME,
                                            msg=new_url,
                                            stat=stats,
                                            statspage="/stats/" + request_path[1:])
                            else:
                                self._db.add_logentry_to_database(request_path[1:])
                                self._send_301(result)
                                return
                        elif blocked:
                            template_filename = self._get_config_template('blocked')
                            text = read_template(
                                        template_filename,
                                        title=SERVER_NAME,
                                        header=SERVER_NAME,
                                        comment=blocked[3])
                        else:
                            self._send_404(header_only)
                            return
                    else:
                        self._send_404(header_only)
                        return
        self._send_response(text, 200, header_only)

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
            # First we check, whether the formular has been filled by
            # something behaving like a bot
            if form.has_key('URL'):
                template_filename = self._get_config_template('homepage')
                text = read_template(
                    template_filename,
                    title=SERVER_NAME,
                    header=SERVER_NAME,
                    msg='<p class="warning">Please check your input</p>')
            else:
                url = form['real_URL'].value if form.has_key('real_URL') else None
                tmp = self._insert_url_to_db(url)
                if tmp:
                    blocked = self._db.is_hash_blocked(tmp)
                    if tmp < 0:
                        self._send_database_problem()
                        return
                    elif blocked:
                        template_filename = self._get_config_template('blocked')
                        text = read_template(
                                    template_filename,
                                    title=SERVER_NAME,
                                    header=SERVER_NAME,
                                    comment=blocked[3])
                    else:
                        template_filename = self._get_config_template('return')
                        text = read_template(
                                template_filename,
                                title='%s - Short URL Result' % SERVER_NAME,
                                header='new URL',
                                path = tmp,
                                hostname = self.server.hostname)
                else:
                    # There was a general issue with URL
                    template_filename = self._get_config_template('homepage')
                    text = read_template(
                        template_filename,
                        title=SERVER_NAME,
                        header=SERVER_NAME,
                        msg='''<p class="warning">Please check your input.</p>''')
        elif self.path == '/ContactUs':
            if form.has_key('URL'):
                # Here we might have a bot who likes to send the webmaster some spam
                # who most likely will be not amused about.
                template_filename = self._get_config_template('contactUsResult')
                text = read_template(
                    template_filename,
                    title='',
                    header='Mail NOT sent',
                    msg='There was an issue with your request. Are you a bot? '
                    '<a href="/ContactUs">Please try again</a>.')
            else:
                try:
                    email = form['email'].value
                    subj = form['subject'].value
                    descr = form['request'].value
                    if self._send_mail(subj, descr, email):
                        template_filename = self._get_config_template('contactUsResult')
                        text = read_template(
                            template_filename,
                            title='',
                            header='Mail sent',
                            msg="Your request has been sent. You will receive an answer soon.")
                    else:
                        self._send_internal_server_error()
                        return
                except KeyError:
                    template_filename = self._get_config_template('contactUsResult')
                    text = read_template(
                        template_filename,
                        title='',
                        header='Mail NOT sent',
                        msg='It appers you did not fill out all needed fields.\
                            <a href="/ContactUs">Please try again</a>.')

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
                except YuDatabaseError:
                    self._send_database_problem(header_only=False)
                    return
                template_filename = self._get_config_template('showpage')
                if result:
                    new_url = '<p><a href="%(result)s">%(result)s</a></p>' % \
                              {'result':result}
                else:
                    new_url = '<p class="warning">No URL found for this string. Please double check your\
                                <a href="/ShowURL">input and try again</a></p>'

                stats = self._db.get_statistics_for_hash(short_url)

                text = read_template(
                    template_filename,
                    title=SERVER_NAME,
                    header=SERVER_NAME,
                    msg=new_url,
                    stat=stats,
                    statspage="/stats/" + short_url)
            else:
                self._send_404()
                return

        else:
            self._send_404()
            return

        self._send_response(text, 200)
    #----------------------------------------------------------------------
    def do_HEAD(self):
        """
        First attempt to implement HEAD response which is pretty much
        the same as the do_GET at the moment w/o sending the real
        data.... As so, we only need to call do_GET with parameter.
        """
        self.do_GET(header_only=True)
