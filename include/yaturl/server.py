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
from threading import Event
from yaturl import config
from yaturl.requesthandler import YuRequestHandler


########################################################################
class YuServer(ThreadingMixIn, HTTPServer):
    """
    Simple, threaded HTTP server
    """

    #----------------------------------------------------------------------
    def __init__(self):
        host = config.get('http', 'host')
        port = config.getint('http', 'port')
        HTTPServer.__init__(self, (host, port), YuRequestHandler)

        if config.has_option('http', 'hostname'):
            hostname = config.get('http', 'hostname')
            if port != 80:
                hostname = '%s:%s' % (hostname, port)
        else:
            # TODO we could get the hostname from the IP the server is
            # bound to if we want this, for now we use a stupid fallback
            hostname = 'yaturl.net'

        # store important information here to be able to access it in the request handler
        self.hostname = hostname
        self.resolve_clients = config.getboolean('http', 'resolve_clients')
        self.log_ip_activated = config.getboolean('main', 'log_ip_activated')
        self._shutdown = Event()

    #----------------------------------------------------------------------
    def serve_forever(self):
        self.socket.settimeout(0.5)
        while not self._shutdown.isSet():
            self.handle_request()

    #----------------------------------------------------------------------
    def shutdown(self):
        self._shutdown.set()
