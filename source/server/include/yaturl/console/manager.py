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


from yaturl.helpers.logger import get_logger
from yaturl.console.server import TelnetInteractiveConsoleServer
from yaturl.console.monitor import SystemMonitor


########################################################################
class ConsoleManager(object):
    """
    Console Manager
    """

    #----------------------------------------------------------------------
    def __init__(self, host, port):
        """"""
        self._host = host
        self._port = port
        self._locals = None
        self._logger = get_logger()
        self._telnet_server = TelnetInteractiveConsoleServer(
            self._host, self._port, self._locals, self._logger)

    #----------------------------------------------------------------------
    def set_locals(self, locals_):
        self._locals = locals_

    #----------------------------------------------------------------------
    def get_telnet_server(self):
        return self._telnet_server

    #----------------------------------------------------------------------
    @classmethod
    def get_system_status(cls):
        monitor = SystemMonitor()
        threads = monitor.get_running_threads()
        uptime = monitor.get_uptime()
        pool = monitor.get_connection_pool()
        load = monitor.get_load_avg()
        time_usr, time_sys  = monitor.get_resource_usage()
        rss  = monitor.get_memory_usage()

        print 'Uptime: %s days, %s' % (uptime['uptime_days'], uptime['uptime_rest'])
        print 'Time USR: %0.2f' % time_usr
        print 'Time SYS: %0.2f' % time_sys
        print 'Memory (RSS): %0.2f MB' % (rss)
        print 'Load: %0.2f %0.2f %0.2f' % load
        print 'DB Pool: %s' % pool
        print 'Running threads:'
        for running_thread in threads:
            print '   %s' % running_thread

    #----------------------------------------------------------------------
    def _start_telnet_server(self):
        self._logger.debug(u'Telnet Console Server started')
        self._telnet_server.set_locals(self._locals)
        self._telnet_server.accept_interactions()

    #----------------------------------------------------------------------
    def serve_forever(self):
        """
        Start the telnet server
        """
        try:
            self._start_telnet_server()
        except Exception:
            self._logger.error('An error occurred', exc_info=True)
            raise

    #----------------------------------------------------------------------
    def shutdown(self):
        """Initiate shutdown of the telnet server"""
        self._logger.debug(u'Telnet Console Server stopping')
        self._telnet_server.stop()
