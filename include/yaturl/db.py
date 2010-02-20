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

import MySQLdb
from MySQLdb.constants.ER import DUP_ENTRY
from safedb import SafeMySQLConnection
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
    def __init__(self, config, logger):
        # we don't check whether the config has this item, it is an
        # error if it is missing
        self._user = config.get('database', 'user')
        self._passwd = config.get('database', 'password')
        self._host = config.get('database', 'host')
        self._port = config.getint('database', 'port')
        self._database = config.get('database', 'database')
        self._conn = None
        self.logger = logger

    #----------------------------------------------------------------------
    def __del__(self):
        self._close()

    #----------------------------------------------------------------------
    def _close(self):
        """
        Safely close the database connection if it exists.
        """
        if self._conn:
            try:
                self._conn.close()
            except MySQLdb.DatabaseError:
                pass
            self._conn = None

    #----------------------------------------------------------------------
    def _open(self, hostname, database=''):
        """
        Open the database connection.
        """
        try:
            conn = SafeMySQLConnection(host=hostname, db=database, user=self._user, passwd=self._passwd,
                port=self._port, use_unicode=True, charset='utf8',
                init_command='SET TRANSACTION ISOLATION LEVEL READ COMMITTED',
                logger=self.logger)
        except MySQLdb.DatabaseError, e:
            self.logger.warn('Database error: %s' % e)
            raise YuDbError('Database error: %s' % e)

        return conn

    #----------------------------------------------------------------------
    def _get_connection(self):
        """
        Return the existing connection or open a new one
        """
        if not self._conn:
            self._conn = self._open(self._host)

        c = self._conn.cursor()
        return (self._conn, c)

    #-------------------------------------------------------------------------
    def get_short_for_hash_from_db(self, hash):
        """
        Checks, whether a short hash is already stored inside
        database. If its stored, the function will return the hash for
        this shorthash
        """
        try:
            conn, c = self._get_connection()
            c.execute('''SELECT link.link_shorthash
                         FROM %s.link
                         WHERE link.link_hash='%s' LIMIT 1''' % (self._database, hash))
            result = c.fetchone()
            c.close()
            return result
        except MySQLdb.DatabaseError, e:
            self.logger.warn('Database error: %s' % e)
            raise YuDbError('Database error: %s' % e)

    #----------------------------------------------------------------------
    def get_link_from_db(self, hash):
        """
        Fetches the link from database based on given hash
        """
        try:
            conn, c = self._get_connection()
            c.execute('''SELECT link.link_link
                         FROM %s.link
                         WHERE link.link_shorthash='%s' LIMIT 1''' % (self._database, hash))
            result = c.fetchone()
            c.close()
            return result
        except MySQLdb.DatabaseError, e:
            self.logger.warn('Database error: %s' % e)
            raise YuDbError('Database error: %s' % e)

    #-------------------------------------------------------------------
    def is_hash_in_db(self, hash):
        """
        Returns the link ID for a hash in case of its available inside
        database.
        """
        try:
            conn, c = self._get_connection()
            c.execute('''SELECT link.link_id
                         FROM %s.link
                         WHERE link.link_hash='%s' ''' % (self._database, hash))
            result = c.fetchone()
            c.close()
            return result
        except MySQLdb.DatabaseError, e:
            self.logger.warn('Database error: %s' % e)
            raise YuDbError('Database error: %s' % e)

    #-------------------------------------------------------------------
    def is_shorthash_in_db(self, short):
        """
        Checks whether a shorthash is stored inside database. If so,
        its returning the link ID of database entry.
        """
        try:
            conn, c = self._get_connection()
            c.execute('''SELECT link.link_id
                         FROM %s.link
                         WHERE link.link_shorthash='%s' ''' % (self._database, short))
            result = c.fetchone()
            c.close()
            return result
        except MySQLdb.DatabaseError, e:
            self.logger.warn('Database error: %s' % e)
            raise YuDbError('Database error: %s' % e)

    #-------------------------------------------------------------------
    def add_link_to_db(self, hash, link):
        """
        Takes the given hash and link and put it into database.
        """
        for i in range(4, len(hash)):
            short = hash[:i]
            try:
                conn, c = self._get_connection()
                link = link.replace("'","")
                c.execute("""INSERT INTO %s.`link`
                         (`link_shorthash`,`link_hash`,`link_link`)
                         VALUES ('%s', '%s', '%s')""" %
                         (self._database, short, hash, link))
                conn.commit()
                c.close()
                return short
            except MySQLdb.DatabaseError, e:
                if e.args and e.args[0] == DUP_ENTRY:
                    if e[1].endswith("key 2"):
                        return self.get_short_for_hash_from_db(hash)
                    if e[1].endswith("key 1"):
                        break
                else:
                    self.logger.warn('Database error: %s' % e)
                    raise YuDbError('Database error: %s' % e)
