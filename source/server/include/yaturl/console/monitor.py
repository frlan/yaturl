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
from yaturl.database.database import YuDatabase
from threading import enumerate as thread_enumerate
from math import floor
from os import getloadavg, getpid
from resource import getrusage, RUSAGE_SELF
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
    def get_load_avg(self):
        """
        Return the load average of the system

        | **return** loadavg (seq of float)
        """
        return getloadavg()

    #----------------------------------------------------------------------
    def get_resource_usage(self):
        """
        Return information about consumed time in user/system mode

        | **return** resource_usage (seq of float)
        """
        resources = getrusage(RUSAGE_SELF)
        return resources.ru_utime, resources.ru_stime

    #----------------------------------------------------------------------
    def get_memory_usage(self):
        """
        Return memory usage information, in MB

        | **return** mem_usage (float)
        """
        proc_status = '/proc/%d/status' % getpid()
        try:
            file_h = open(proc_status)
            content = file_h.read()
            file_h.close()
        except IOError:
            return 0.0
        lines = content.strip().split('\n')
        for line in lines:
            if line.startswith('VmRSS:'):
                values = line.split(':')
                vmrss = values[1].strip()
                try:
                    vmrss = vmrss.split()[0]
                    vmrss = vmrss.strip()
                    return float(vmrss) / 1024
                except IndexError:
                    return 0.0

        return 0.0

    #----------------------------------------------------------------------
    def get_connection_pool(self):
        """
        Return the status of the SQLAlchemy connection pool

        | **return** status (str)
        """
        connection_pool = YuDatabase.get_connection_pool()
        return connection_pool.status() if connection_pool else None

    #----------------------------------------------------------------------
    def get_uptime(self):
        """
        Return the uptime of the whole backend

        | **return** uptime (dict{str type: mixed value})
        """
        uptime = float(time() - start_time)
        if uptime > 0:
            uptime_days = int(floor(uptime / 86400))
            t_val = gmtime(uptime - (uptime_days * 86400))
            return dict(uptime=uptime,
                        uptime_days=uptime_days,
                        uptime_rest=strftime('%H:%M:%S', t_val))
