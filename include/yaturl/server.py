#!/usr/bin/env python
# -*- coding: utf-8 -*-


from BaseHTTPServer import HTTPServer
from SocketServer import ThreadingMixIn
from yaturl.db import YuDb
from yaturl.requesthandler import YuRequestHandler
import os

# TODO test threading

class YuServer(ThreadingMixIn, HTTPServer):

    def __init__(self, config, errorlog, accesslog):
        host = config.get('http', 'host')
        port = config.getint('http', 'port')
        HTTPServer.__init__(self, (host, port), YuRequestHandler)

        # store important information here to be able to access it in the request handler
        self.config = config
        self.errorlog = errorlog
        self.accesslog = accesslog
        self.resolve_clients = config.get('http', 'resolve_clients')
        # create a database object, the connection is established automatically when needed
        self.db = YuDb(config)


