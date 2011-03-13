# -*- coding: utf-8 -*-
"""$Id$"""

from MySQLdb import OperationalError, connect
from MySQLdb.constants.CR import SERVER_GONE_ERROR, SERVER_LOST
from sqlalchemy.pool import QueuePool


########################################################################
class ConnectionCreator(object):

    #----------------------------------------------------------------------
    def __init__(self, config):
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
def factor_database_connection_pool(config):
    creator = ConnectionCreator(config)
    pool_size = config.getint('database', 'pool_size')
    max_overflow = config.getint('database', 'max_overflow')

    return FreshConnectionQueuePool(creator, pool_size=pool_size, max_overflow=max_overflow)
