# -*- coding: utf-8 -*-


import MySQLdb
from MySQLdb.constants.CR import SERVER_GONE_ERROR
import sys


class YuDbError(Exception):
    """
    Generic database error
    """


class YuDb(object):
    """
    Very simple wrapper class around MySQLdb for convenience.
    """
    #----------------------------------------------------------------------
    def __init__(self, config):
        # we don't check whether the config has this item, it is an error if it is missing
        self._user = config.get('database', 'user')
        self._passwd = config.get('database', 'password')
        self._host = config.get('database', 'host')
        self._port = config.getint('database', 'port')
        self._database = config.get('database', 'database')
        self._conn = None
        # if the database connection died, retry it twice, then give up
        self._conn_retry_count = 3

    #----------------------------------------------------------------------
    def __del__(self):
        if self._conn:
            self._close(self._conn)

    #----------------------------------------------------------------------
    def _open(self, hostname, database=''):
        """
        Open the database connection.
        """
        try:
            conn = MySQLdb.connect(host=hostname, db=database, user=self._user, passwd=self._passwd,
                port=self._port, use_unicode=True, init_command='SET NAMES utf8')
            c = conn.cursor()
            self._conn_retry_count = 3
        except MySQLdb.DatabaseError, e:
            raise YuDbError('Database error: %s' % e)

        return (conn, c)

    #----------------------------------------------------------------------
    def _get_connection(self):
        """
        Return the existing connection or open a new one
        """
        if not self._conn:
            self._conn = self._open(self._host)

        return self._conn

    #----------------------------------------------------------------------
    def _close(self, x):
        """
        Close the database connection.
        """
        conn, c = x
        try:
            c.close()
            conn.close()
        except MySQLdb.DatabaseError:
            pass

    #----------------------------------------------------------------------
    def get_link_from_db(self, hash):
        """
        Fetches the link from database based on given hash
        """
        try:
            conn, c = self._get_connection()
            c.execute('''SELECT l.link_link
                         FROM %s.link as l
                         WHERE l.link_shorthash='%s' LIMIT 1''' % (self._database, hash))
            return c.fetchone()
        except MySQLdb.DatabaseError, e:
            if e.args and e.args[0] == SERVER_GONE_ERROR and self._conn_retry_count > 0:
                self._conn_retry_count -= 1
                # trigger establishing a new connection on the next run
                self._conn_ax1 = None
                return self.get_link_from_db(hash)
            else:
                raise YuDbError('Database error: %s' % e)

    #-------------------------------------------------------------------
    def is_hash_in_db(self, hash):
        try:
            conn, c = self._get_connection()
            c.execute('''SELECT l.link_id
                         FROM %s.link as l
                         WHERE l.link_hash='%s' ''' % (self._database, hash))
            return c.fetchone()
        except MySQLdb.DatabaseError, e:
            if e.args and e.args[0] == SERVER_GONE_ERROR and self._conn_retry_count > 0:
                self._conn_retry_count -= 1
                # trigger establishing a new connection on the next run
                self._conn_ax1 = None
                return self.is_hash_in_db(hash)
            else:
                raise YuDbError('Database error: %s' % e)

    #-------------------------------------------------------------------
    def is_shorthash_in_db(self, short):
        try:
            conn, c = self._get_connection()
            c.execute('''SELECT l.link_id
                         FROM %s.link as l
                         WHERE l.link_shorthash='%s' ''' % (self._database, short))
            return c.fetchone()
        except MySQLdb.DatabaseError, e:
            if e.args and e.args[0] == SERVER_GONE_ERROR and self._conn_retry_count > 0:
                self._conn_retry_count -= 1
                # trigger establishing a new connection on the next run
                self._conn_ax1 = None
                return self.is_shorthash_in_db(short)
            else:
                raise YuDbError('Database error: %s' % e)

    #-------------------------------------------------------------------
    def add_link_to_db(self, short, hash, link):
        """
        Takes the given hash and link and put it into database.
        """
        try:
            conn, c = self._get_connection()
            c.execute('''INSERT INTO %s.`link` (
                        `link_shorthash`,`link_hash`,`link_link`)
                         VALUES ('%s', '%s','%s')''' % (self._database, short, hash, link))
        except MySQLdb.DatabaseError, e:
            if e.args and e.args[0] == SERVER_GONE_ERROR and self._conn_retry_count > 0:
                self._conn_retry_count -= 1
                # trigger establishing a new connection on the next run
                self._conn_ax1 = None
                return self.add_link_to_db(short, hash, link)
            else:
                raise YuDbError('Database error: %s' % e)
