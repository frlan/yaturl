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


import console


########################################################################
class TelnetInteractiveConsoleServer(console.TelnetInteractiveConsoleServer):

    #----------------------------------------------------------------------
    def __init__(self, host='127.0.0.1', port=7070, locals_=None, logger=None):
        super(TelnetInteractiveConsoleServer, self).__init__(host, port, locals_)
        self._logger = logger
        self._running = False

    #----------------------------------------------------------------------
    def set_locals(self, locals_):
        """"""
        if not self._running:
            self.locals_ = locals_
        else:
            raise ValueError, 'Server already started'

    #----------------------------------------------------------------------
    def accept_interactions(self):
        self._running = True
        super(TelnetInteractiveConsoleServer, self).accept_interactions()

    #----------------------------------------------------------------------
    def client_connect(self, client):
        address = client.getpeername()
        self._logger.info('Client "%s:%s" connected to telnet service' % address)

    #----------------------------------------------------------------------
    def client_disconnect(self, client):
        address = client.getpeername()
        self._logger.info('Client "%s:%s" disconnected from telnet service' % address)



