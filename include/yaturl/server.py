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


from BaseHTTPServer import HTTPServer
from SocketServer import ThreadingMixIn
from yaturl.db import YuDb
from yaturl.requesthandler import YuRequestHandler


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
        self.db = YuDb(config, errorlog)


