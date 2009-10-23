#!/usr/bin/env python
# -*- coding: utf-8 -*-


from BaseHTTPServer import BaseHTTPRequestHandler
import socket
import cgi
import yaturltemplate

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
    def _get_text(self, method):
        return text % { 'path': self.path, 'method': method }

    #----------------------------------------------------------------------
    def _send_head(self, text):
        self.send_response(200)
        self.send_header('Content-Type', 'text/html')
        self.send_header("Content-Length", len(text))
        self.end_headers()

    #----------------------------------------------------------------------
    def do_GET(self):
        text = yaturltemplate.template(self.server.config.get('main','statichomepage'),
            {'path': self.path,
            'method': "get" })
        self._send_head(text)
        self.wfile.write(text)

    #----------------------------------------------------------------------
    def do_POST(self):
        form = cgi.FieldStorage(
            fp=self.rfile,
            headers=self.headers,
            environ={'REQUEST_METHOD':'POST'})

        ## Begin the response
        self.send_response(200)
        text = yaturltemplate.template(self.server.config.get('main','staticresultpage'),
            {'URL': form['URL'].value})
        self._send_head(text)
        self.end_headers()
        self.wfile.write(text)

    #----------------------------------------------------------------------
    def do_HEAD(self):
        text = self._get_text('head')
        self._send_head(text)


