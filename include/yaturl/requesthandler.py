#!/usr/bin/env python
# -*- coding: utf-8 -*-

from BaseHTTPServer import BaseHTTPRequestHandler
import socket
import cgi
import hashlib
import yaturlTemplate
from db import YuDbError

# we need to hard-code this one at least in case of the file cannot be found on disk
template_500 = '''<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
  "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">

<head>
	<title>yatURL.net - Internal server error</title>
	<meta http-equiv="content-type" content="text/html;charset=utf-8" />
	<meta name="generator" content="Geany 0.18" />
</head>

<body>
	<p>500 - Internal server error</p>

	<p>The server encountered an internal error and was unable to complete your request.</p>
</body>
</html>
'''

class YuRequestHandler(BaseHTTPRequestHandler):

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
    def log_message(self, format, *args):
        """
        Overwrite the default log_message() method which prints for
        some reason to stderr which we don't want.  Instead, use a
        logger.
        """
        format = '%s: %s' % (self.address_string(), format)
        self.server.accesslog.info(format%args)

    #----------------------------------------------------------------------
    def _send_head(self, text, code):
        self.send_response(code)
        if self.path.endswith(".css"):
            self.send_header('Content-Type', 'text/css')
        else:
            self.send_header('Content-Type', 'text/html')
        self.send_header("Content-Length", len(text) +1 )
        self.end_headers()

    #----------------------------------------------------------------------
    def _send_404(self):
        text = yaturlTemplate.template(
            self.server.config.get('templates','corruptlink'),
            URL="Nothing")
        if text:
            self._send_head(text, 404)
            self.end_headers()
            try:
                self.wfile.write(text)
            except socket.error:
                # clients like to stop reading after they got a 404
                pass
        else:
            self._send_internal_server_error()

    #----------------------------------------------------------------------
    def _send_internal_server_error(self):
        text = yaturlTemplate.template(self.server.config.get('templates','servererror'))
        if not text:
            # fallback to hard-coded template
            text = template_500
        self._send_head(text, 500)
        self.end_headers()
        self.wfile.write(text)

    #----------------------------------------------------------------------
    def _send_database_problem(self):
        text = yaturlTemplate.template(self.server.config.get('templates','databaseissuelink'))
        if not text:
            self._send_internal_server_error()
            return
        self._send_head(text, 500)
        self.end_headers()
        self.wfile.write(text)

    #----------------------------------------------------------------------
    def do_GET(self):
        # Homepage and other path ending with /
        # Needs to be extended later with things like FAQ etc.
        if self.path.endswith("/"):
            text = yaturlTemplate.template(
                self.server.config.get('templates','statichomepage'),
                msg="")
            if text:
                self._send_head(text, 200)
                self.end_headers()
                self.wfile.write(text)
            else:
                self._send_internal_server_error()

        # TODO: Avoid reactng on manipulated realtive path as
        # e.g. /static/../etc/yaturl.conf
        elif self.path.find("/static/") > -1:
            try:
                file = open(self.path[1:])
                text = file.read()
                self._send_head(text, 200)
                self.end_headers()
                self.wfile.write(text)
            except IOError:
                self._send_404()
        # Every other page
        else:
            # Assuming, if there is aynthing else then a alphanumeric
            # character after the starting /, its not a valid hash in
            # no case
            if self.path[1:].isalnum():
                try:
                    result = self.server.db.get_link_from_db(self.path[1:])
                except YuDbError:
                    self._send_database_problem()
                    return
                if result is not None:
                    self.send_response(301)
                    self.send_header('Location', result[0])
                    self.send_header('Content-type', 'text/html')
                    self.end_headers()
                else:
                    self._send_404()
            else:
                self._send_404()

    #----------------------------------------------------------------------
    def do_POST(self):
        form = cgi.FieldStorage(
            fp=self.rfile,
            headers=self.headers,
            environ={'REQUEST_METHOD':'POST'})
        # TODO: Check for valid URL and avoid SQL injection later
        # inisde this function
        if 'URL' in form:
            # Calculating the output
            url = form['URL'].value
            # First check, whether some protocoll prefix is
            # available. If not, assume http:// was intented to put
            # there.
            if not url.find("://") > -1:
                url = 'http://%s' % (url)
            hash = hashlib.sha1(url).hexdigest()
            # Begin the response
            try:
                result = self.server.db.is_hash_in_db(hash)
            except YuDbError:
                self._send_database_problem()
                return
            if not result:
                try:
                    short = self.server.db.add_link_to_db(hash, url)
                except YuDbError:
                    self._send_database_problem()
                    return
                new_URL= '<a href="http://yaturl.net/%s">http://yaturl.net/%s</a>' % (short,short)
                text = yaturlTemplate.template(
                       self.server.config.get('templates','staticresultpage'),
                       URL=new_URL)
            else:
                # It appears link is already stored or you have found
                # an collision on sha1
                try:
                    short = self.server.db.get_short_for_hash_from_db(hash)[0]
                except YuDbError:
                    self._send_database_problem()
                    return
                new_URL= '<a href="http://yaturl.net/%s">http://yaturl.net/%s</a>' % (short,short)
                text = yaturlTemplate.template(
                       self.server.config.get('templates','staticresultpage'),
                       URL=new_URL)
        else:
            text = yaturlTemplate.template(
            self.server.config.get('templates','statichomepage'), msg="<p>Please specify any input</p>")

        if text:
            self._send_head(text, 200)
            self.end_headers()
            self.wfile.write(text)
        else:
            self._send_internal_server_error()

