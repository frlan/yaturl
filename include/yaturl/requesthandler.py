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
        self.send_header('Content-Type', 'text/html')
        self.send_header("Content-Length", len(text))
        self.end_headers()

    #----------------------------------------------------------------------
    def do_GET(self):
        # Homepage and other path ending with /
        # Needs to be extended later with things like FAQ etc.
        if self.path.endswith("/"):
            text = yaturlTemplate.template(
                self.server.config.get('templates','statichomepage'),
                msg="",
                host=self.server.config.get('host','hosturl'))

        # Every other page
        else:
            result = self.server.db.get_link_from_db(self.path[1:])
            if result is not None:
                text = yaturlTemplate.template(
                    self.server.config.get('templates','resultpage'),
                    URL=result[0], method="get")
            else:
                text = yaturlTemplate.template(
                    self.server.config.get('templates','corruptlink'),
                    URL="Nothing")

        self._send_head(text)
        self.wfile.write(text)

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
                print "hash passed"
                for i in range(1, len(hash)):
                    print hash[0:i]
                    if not self.server.db.is_shorthash_in_db(hash[0:i]):
                        self.server.db.add_link_to_db(hash[:i], hash, form['URL'].value)
                        text = yaturlTemplate.template(
                            self.server.config.get('templates','staticresultpage'),
                            URL=hash[0:i])
                    break
            else:
                text = yaturlTemplate.template(
                    self.server.config.get('templates','staticresultpage'),
                    URL="Error!")
            # It appears link is already stored or you have found an collision on sha1

        else:
            text = yaturlTemplate.template(
            self.server.config.get('templates','statichomepage'),
                msg="Please specify any input",
                host=self.server.config.get('host','hosturl'))

        self._send_head(text)
        self.end_headers()
        self.wfile.write(text)

    #----------------------------------------------------------------------
    def do_HEAD(self):
        text = self._get_text('head')
        self._send_head(text)

