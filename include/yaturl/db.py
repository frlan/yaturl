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

from yaturl.constants import MYSQL_CONNECTION_POOL_SIZE
import sqlalchemy.pool as pool
import MySQLdb as MySQLdb_orig
# proxy MySQLdb module to enable SQLAlchemy's connection pooling
MySQLdb = pool.manage(MySQLdb_orig,
    pool_size=MYSQL_CONNECTION_POOL_SIZE,
    max_overflow=5,
    echo=True)

from MySQLdb.constants.ER import DUP_ENTRY
from MySQLdb.constants.CR import SERVER_GONE_ERROR, SERVER_LOST


class YuDbError(MySQLdb.DatabaseError):
    """
    Generic database error
    """
    #----------------------------------------------------------------------
    def __init__(self, msg):
        super(YuDbError, self).__init__()
        self._msg = msg

    #----------------------------------------------------------------------
    def __str__(self):
        return u"Database Error: %s" % self._msg



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
        self._hostname = config.get('database', 'host')
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
    def _open(self):
        """
        Open the database connection.

        | **return** conn (SafeMySQLConnection)
        """
        retry_count = MYSQL_CONNECTION_POOL_SIZE
        while retry_count > 0:
            try:
                conn = MySQLdb.connect(host=self._hostname, db=self._database, user=self._user,
                    passwd=self._passwd,
                    port=self._port, use_unicode=True, charset='utf8',
                    init_command='SET TRANSACTION ISOLATION LEVEL READ COMMITTED')
                conn.cursor().execute('SET time_zone = "+00:00";')
            except MySQLdb.DatabaseError, e:
                if e.args and (e.args[0] == SERVER_GONE_ERROR or e.args[0] == SERVER_LOST) and \
                        retry_count > 0:
                    retry_count -= 1
                    # try again by requesting another connection from the pool
                    continue
                else:
                    self.logger.warn('Database error: %s' % e)
                    raise YuDbError(str(e))
            break

        return conn

    #----------------------------------------------------------------------
    def _get_connection(self):
        """
        Return the existing connection or open a new one

        | **return** connection, cursor (SafeMySQLConnection, MySQLdb.Cursor)
        """
        if not self._conn:
            self._conn = self._open()

        cursor = self._conn.cursor()
        return (self._conn, cursor)

    #-------------------------------------------------------------------------
    def get_short_for_hash_from_db(self, url_hash):
        """
        Checks, whether a short hash is already stored in the
        database. If it is stored, the function will return the hash for
        this shorthash, otherwise None

        | **param** url_hash (str)
        | **return** short_hash (str)
        """
        try:
            cursor = self._get_connection()[1]
            cursor.execute('''SELECT `link`.`link_shorthash`
                         FROM `link`
                         WHERE `link`.`link_hash` = %s LIMIT 1''', (url_hash))
            result = cursor.fetchone()
            cursor.close()
            if result:
                return result[0]
        except MySQLdb.DatabaseError, e:
            self.logger.warn('Database error: %s' % e)
            raise YuDbError(str(e))

    #----------------------------------------------------------------------
    def get_link_from_db_by_complete_hash(self, url_hash):
        """
        Fetches the link from database based on given complete url_hash

        | **param** url_hash (str)
        | **return** url (str)
        """
        try:
            cursor = self._get_connection()[1]
            cursor.execute('''SELECT `link`.`link_link`
                         FROM `link`
                         WHERE `link`.`link_hash` = %s LIMIT 1''', (url_hash))
            result = cursor.fetchone()
            cursor.close()
            if result:
                return result[0]
        except MySQLdb.DatabaseError, e:
            self.logger.warn('Database error: %s' % e)
            raise YuDbError(str(e))

    #----------------------------------------------------------------------
    def get_link_from_db(self, url_hash):
        """
        Fetches the link from database based on given url_hash

        | **param** url_hash (str)
        | **return** url (str)
        """
        try:
            cursor = self._get_connection()[1]
            cursor.execute('''SELECT `link`.`link_link`
                         FROM `link`
                         WHERE `link`.`link_shorthash` = %s LIMIT 1''', (url_hash))
            result = cursor.fetchone()
            cursor.close()
            if result:
                return result[0]
        except MySQLdb.DatabaseError, e:
            self.logger.warn('Database error: %s' % e)
            raise YuDbError(str(e))

    #-------------------------------------------------------------------
    def is_hash_in_db(self, url_hash):
        """
        Returns the link ID for a hash in case of it's available in the
        database.

        | **param** url_hash (str)
        | **return** link_id (int)
        """
        try:
            cursor = self._get_connection()[1]
            cursor.execute('''SELECT `link`.`link_id`
                         FROM `link`
                         WHERE `link`.`link_hash` = %s''', (url_hash))
            result = cursor.fetchone()
            cursor.close()
            if result:
                return result[0]
        except MySQLdb.DatabaseError, e:
            self.logger.warn('Database error: %s' % e)
            raise YuDbError(str(e))

    #-------------------------------------------------------------------
    def is_shorthash_in_db(self, short):
        """
        Checks whether a shorthash is stored in the database. If so,
        it returns the link ID of the database entry.

        | **param** short (str)
        | **return** link_id (int)
        """
        try:
            cursor = self._get_connection()[1]
            cursor.execute('''SELECT `link`.`link_id`
                         FROM `link`
                         WHERE `link`.`link_shorthash` = %s''', (short))
            result = cursor.fetchone()
            cursor.close()
            if result:
                return result[0]
        except MySQLdb.DatabaseError, e:
            self.logger.warn('Database error: %s' % e)
            raise YuDbError(str(e))

    #-------------------------------------------------------------------
    def add_link_to_db(self, url_hash, link):
        """
        Takes the given hash and link and put it into database.

        | **param** url_hash (str)
        | **param** link (str)
        | **return** short_hash (str)
        """
        for i in range(4, len(url_hash)):
            short = url_hash[:i]
            try:
                conn, cursor = self._get_connection()
                cursor.execute("""INSERT INTO `link`
                         (`link_shorthash`,`link_hash`,`link_link`)
                         VALUES (%s, %s, %s)""",
                         (short, url_hash, link))
                conn.commit()
                cursor.close()
                return short
            except MySQLdb.DatabaseError, e:
                if e.args and e.args[0] == DUP_ENTRY:
                    if e[1].endswith("key 2"):
                        return self.get_short_for_hash_from_db(url_hash)
                    if e[1].endswith("key 1"):
                        break
                else:
                    self.logger.warn('Database error: %s' % e)
                    raise YuDbError(str(e))
