#!/usr/bin/env python
# -*- coding: utf-8 -*-

from BaseHTTPServer import BaseHTTPRequestHandler
import socket
import cgi
import yaturlTemplate
import hashlib

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
        Overwrite the default log_message() method which prints for some reason
        to stderr which we don't want.
        Instead, use a logger.
        """
        format = '%s: %s' % (self.address_string(), format)
        self.server.accesslog.info(format%args)

    #----------------------------------------------------------------------
    def _send_head(self, text):
        self.send_response(200)
        if self.path.endswith(".css"):
            self.send_header('Content-Type', 'text/css')
        else:
            self.send_header('Content-Type', 'text/html')
        self.send_header("Content-Length", len(text))
        self.end_headers()

    #----------------------------------------------------------------------
    def do_404(self):
        self.send_response(404)
        text = yaturlTemplate.template(
            self.server.config.get('templates','corruptlink'),
            URL="Nothing")
        self._send_head(text)
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
            self.send_response(200)
            self._send_head(text)
            self.end_headers()
            self.wfile.write(text)

        elif self.path.find("/static/") > -1:
            # Try to avoid some unwanted pathes inside static page
            print self.path
            try:
                file = open(self.path[1:])
                text = file.read()
                self.send_response(200)
                self._send_head(text)
                self.end_headers()
                self.wfile.write(text)
            except IOError:
                self.do_404()
        # Every other page
        else:
            print "Something else"
            result = self.server.db.get_link_from_db(self.path[1:])
            if result is not None:
                self.send_response(301)
                self.send_header('Location', result[0])
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self._send_head(text)
                self.wfile.write(text)
                return
            else:
                self.do_404()
                
    #----------------------------------------------------------------------
    def do_POST(self):
        form = cgi.FieldStorage(
            fp=self.rfile,
            headers=self.headers,
            environ={'REQUEST_METHOD':'POST'})
        if 'URL' in form:
            # Calculating the output
            hash = hashlib.sha1(form['URL'].value).hexdigest()
            # Begin the response
            self.send_response(200)
            if not self.server.db.is_hash_in_db(hash):
                short = self.server.db.add_link_to_db(hash, form['URL'].value)
                new_URL= '<a href="http://yaturl.net/%s">http://yaturl.net/%s</a>' % (short,short)
                text = yaturlTemplate.template(
                       self.server.config.get('templates','staticresultpage'),
                       URL=new_URL)
            else:
                # It appears link is already stored or you have found an collision on sha1
                short = self.server.db.get_short_for_hash_from_db(hash)[0]
                new_URL= '<a href="http://yaturl.net/%s">http://yaturl.net/%s</a>' % (short,short)
                text = yaturlTemplate.template(
                       self.server.config.get('templates','staticresultpage'),
                       URL=new_URL)
        else:
            text = yaturlTemplate.template(
            self.server.config.get('templates','statichomepage'),
                msg="Please specify any input",
                host=self.server.config.get('host','hosturl'))

        self._send_head(text)
        self.end_headers()
        self.wfile.write(text)
