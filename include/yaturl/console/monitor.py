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



from yaturl import start_time
from threading import enumerate as thread_enumerate
from math import floor
from time import time, gmtime, strftime


########################################################################
class SystemMonitor(object):
    """Basic system checks and monitoring"""

    #----------------------------------------------------------------------
    def get_running_threads(self):
        """
        Return a list of all running threads

        | **return** running_threads (seq of str)
        """
        return thread_enumerate()

    #----------------------------------------------------------------------
    def get_connection_pool(self):
        """
        Return the status of the SQLAlchemy connection pool

        | **return** status (str)
        """
        # FIXME
        return None

    #----------------------------------------------------------------------
    def get_uptime(self):
        """
        Return the uptime of the whole backend

        | **return** uptime (dict{str type: mixed value})
        """
        uptime = float(time() - start_time)
        if uptime > 0:
            uptime_days = floor(uptime / 86400)
            t_val = gmtime(uptime - (uptime_days * 86400))
            return dict(uptime=uptime,
                        uptime_days=uptime_days,
                        uptime_rest=strftime('%H:%M:%S', t_val))
