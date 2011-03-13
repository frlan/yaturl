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


from MySQLdb import OperationalError, connect
from MySQLdb.constants.CR import SERVER_GONE_ERROR, SERVER_LOST
from sqlalchemy.pool import QueuePool
from yaturl import config


########################################################################
class ConnectionCreator(object):

    #----------------------------------------------------------------------
    def __init__(self):
        self._user = config.get('database', 'user')
        self._passwd = config.get('database', 'password')
        self._hostname = config.get('database', 'host')
        self._port = config.getint('database', 'port')
        self._database = config.get('database', 'database')

    #----------------------------------------------------------------------
    def __call__(self):
        conn = connect(
            host=self._hostname,
            db=self._database,
            user=self._user,
            passwd=self._passwd,
            port=self._port,
            use_unicode=True,
            charset='utf8',
            init_command='SET TRANSACTION ISOLATION LEVEL READ COMMITTED')
        conn.cursor().execute('SET time_zone = "+00:00";')
        return conn


########################################################################
class FreshConnectionQueuePool(QueuePool):
    """
    Before returning any connection from the pool, execute a ping()
    on the connection to verify it's still working and not timed out or whatever.
    """

    #----------------------------------------------------------------------
    def do_get(self):
        connection = QueuePool.do_get(self)
        try:
            self._ping_connection(connection)
        except OperationalError, e:
            if e and e[0] in (SERVER_GONE_ERROR, SERVER_LOST):
                self._establish_new_connection(connection, e)
            else:
                raise
        return connection

    #----------------------------------------------------------------------
    def _establish_new_connection(self, connection, e=None):
        connection.invalidate(e)
        connection.get_connection()

    #----------------------------------------------------------------------
    def _ping_connection(self, connection):
        if connection and connection.connection:
            connection.connection.ping()
        else:
            raise OperationalError, (SERVER_GONE_ERROR, 'Connection lost')


#----------------------------------------------------------------------
def factor_database_connection_pool():
    creator = ConnectionCreator()
    pool_size = config.getint('database', 'pool_size')
    max_overflow = config.getint('database', 'max_overflow')

    return FreshConnectionQueuePool(creator, pool_size=pool_size, max_overflow=max_overflow)
