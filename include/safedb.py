# -*- coding: utf-8 -*-
#
# Author:  Enrico Tröger
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


import MySQLdb
from MySQLdb.constants.CR import SERVER_GONE_ERROR, SERVER_LOST
from MySQLdb.connections import Connection
from MySQLdb.cursors import Cursor
from inspect import stack


class SafeCursor(Cursor):
    """
    Simple wrapper class around the MySQLdb default Cursor class to handle
    'Server gone' and 'Lost connection' errors. In case of these errors,
    the SQL query is executed again after re-establishing the connection.
    """
    #----------------------------------------------------------------------
    def __init__(self, connection, retry_count=3):
        super(SafeCursor, self).__init__(connection)
        # if the database connection died, retry it a few times before giving up
        self._conn_retry_count = retry_count

    #----------------------------------------------------------------------
    def execute(self, query, args=None):
        """
        Wrapper for the default MySQLdb Cursor class' execute() method to catch and
        handle SERVER_LOST and SERVER_GONE_ERROR errors by re-establishing the
        connection.
        """
        try:
            Cursor.execute(self, query, args)
        except MySQLdb.DatabaseError, e:
            if e.args and (e.args[0] == SERVER_GONE_ERROR or e.args[0] == SERVER_LOST) and self._conn_retry_count > 0:
                self._conn_retry_count -= 1
                # establish a new connection
                self.connection.reconnect()
                return self.execute(query, args)
            else:
                # raise all other errors
                raise

    #----------------------------------------------------------------------
    def executemany(self, query, args):
        """
        Wrapper for the default MySQLdb Cursor class' executemany() method to catch and
        handle SERVER_LOST and SERVER_GONE_ERROR errors by re-establishing the
        connection.
        """
        try:
            Cursor.executemany(self, query, args)
        except MySQLdb.DatabaseError, e:
            if e.args and (e.args[0] == SERVER_GONE_ERROR or e.args[0] == SERVER_LOST) and self._conn_retry_count > 0:
                self._conn_retry_count -= 1
                # establish a new connection
                self.connection.reconnect()
                return self.executemany(query, args)
            else:
                # raise all other errors
                raise


class SafeMySQLConnection(Connection):
    """
    Simple wrapper class around the MySQLdb default Connection class to
    provide a reconnect() method.
    """
    Connection.default_cursor = SafeCursor

    #----------------------------------------------------------------------
    def __init__(self, *args, **kwargs):
        """
        Simple wrapper which stores the passed arguments, necessary for reconnect().
        Then the base class' __init__() method is called.
        """
        self.arguments = (args, kwargs)
        if kwargs.has_key('logger'):
            self.logger = kwargs.get('logger', None)
            del kwargs['logger']
        else:
            self.logger = None
        super(SafeMySQLConnection, self).__init__(*args, **kwargs)

    #----------------------------------------------------------------------
    def _do_log(self):
        s = stack()
        try:
            caller = s[3][3]
        except IndexError:
            caller = '(unknown)'
        self.logger.warn('%s: Reconnecting to database due to lost connection' % caller)

    #----------------------------------------------------------------------
    def reconnect(self):
        """
        Implement a reconnect method which closes the current connection and
        call __init__() in order to establish a new connection.
        """
        self.close()
        args, kwargs = self.arguments
        if self.logger:
            self._do_log()
        super(SafeMySQLConnection, self).__init__(*args, **kwargs)

    #----------------------------------------------------------------------
    def cursor(self, cursorclass=None, retry_count=3):
        """
        Create a cursor on which queries may be performed.
        """
        cc = cursorclass or self.cursorclass
        if cc == SafeCursor:
            return cc(self, retry_count)
        else:
            return cc(self)
