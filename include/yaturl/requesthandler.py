#!/usr/bin/env python
# -*- coding: utf-8 -*-

from BaseHTTPServer import BaseHTTPRequestHandler
import socket
import cgi
import yaturlTemplate
import linkHash

hashtable = {
	"a": "http://foo.de",
	"b": "http://baa.de",
	"c": "ftp://ftp.debian.org/"
}

def is_hash_in_table(hash):
	if hash in hashtable:
		print "yepp, we already have it"
		return get_link_from_hash(hash)
	else:
		print "well,not yet"
		return None

def get_link_from_hash(hash):
	if hash in hashtable:
		return hashtable[hash]
	else:
		return None

#def get_hash_from_link(link):
def add_hash(hash, link):
	if is_hash_in_table(hash) is not None:
		print "not adding"
	else:
		print "Should be added, but nothing done"
	

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
				msg="")

		# Every other page
		else:
			if self.path[1:] in hashtable:
				text = yaturlTemplate.template(
				self.server.config.get('templates','resultpage'),
				URL=get_link_from_hash(self.path[1:]), method="get")
			else:
				text = yaturlTemplate.template(
					self.server.config.get('templates','corruptlink'),
					URL=get_link_from_hash(self.path[1:]))
		
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
			link = linkHash.linkHash(newlink = form['URL'].value)

			# Begin the response
			self.send_response(200)
			add_hash(link.hash, link.link)
			text = yaturlTemplate.template(
				self.server.config.get('templates','staticresultpage'),
				URL=link.hash)
		else:
			text = yaturlTemplate.template(
			self.server.config.get('templates','statichomepage'),
				msg="Please specify any input")
		self._send_head(text)
		self.end_headers()
		self.wfile.write(text)

    #----------------------------------------------------------------------
    def do_HEAD(self):
        text = self._get_text('head')
        self._send_head(text)

