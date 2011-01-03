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
from MySQLdb import DatabaseError
import sqlalchemy.pool as pool
import MySQLdb as MySQLdb_orig
# proxy MySQLdb module to enable SQLAlchemy's connection pooling
MySQLdb = pool.manage(MySQLdb_orig,
    pool_size=MYSQL_CONNECTION_POOL_SIZE,
    max_overflow=5,
    echo=True)

from MySQLdb.constants.ER import DUP_ENTRY
from MySQLdb.constants.CR import SERVER_GONE_ERROR, SERVER_LOST


class YuDbError(DatabaseError):
    """
    Generic database error
    """
    #----------------------------------------------------------------------
    def __init__(self, msg):
        DatabaseError.__init__(self)
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

    #-------------------------------------------------------------------
    def get_link_details(self, shorthash):
        """
        Returns a list with complete details of given link.
        """
        try:
            cursor = self._get_connection()[1]
            cursor.execute('''SELECT `link`.`link_id`,
                                     `link`.`link_shorthash`,
                                     `link`.`link_hash`,
                                     `link`.`link_link`,
                                     `link`.`link_comment`,
                                     `link`.`entry_date`
                         FROM `link`
                         WHERE `link`.`link_shorthash` = %s  LIMIT 1 ''', (shorthash))
            result = cursor.fetchone()
            cursor.close()
            if result:
                return result
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
                         WHERE `link`.`link_shorthash` = %s  LIMIT 1 ''', (url_hash))
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
    def get_link_creation_timestamp(self, shorthash):
        """
        Return the creation timestamp of the link based on its shorthash

        | **param** shorthash (str)
        | **return** timestamp (datetime)
        """
        try:
            cursor = self._get_connection()[1]
            cursor.execute('''SELECT `link`.`entry_date`
                         FROM `link`
                         WHERE `link`.`link_shorthash` = %s''', (shorthash))
            result = cursor.fetchone()
            cursor.close()
            return result
        except MySQLdb.DatabaseError, e:
            self.logger.warn('Database error: %s' % e)
            raise YuDbError(str(e))

    #-------------------------------------------------------------------
    def is_shorthash_in_db(self, shorthash):
        """
        Checks whether a shorthash is stored in the database. If so,
        it returns the link ID of the database entry.

        | **param** shorthash (str)
        | **return** link_id (int)
        """
        try:
            cursor = self._get_connection()[1]
            cursor.execute('''SELECT `link`.`link_id`
                         FROM `link`
                         WHERE `link`.`link_shorthash` = %s''', (shorthash))
            result = cursor.fetchone()
            cursor.close()
            if result:
                return result[0]
        except MySQLdb.DatabaseError, e:
            self.logger.warn('Database error: %s' % e)
            raise YuDbError(str(e))

    #-------------------------------------------------------------------
    def is_hash_blocked(self, shorthash):
        """
        Checks whether given (short) hash is marked as blocked and is returning
        some data about. If its not blocked, its just returning none.

        | **param** shorthash (str)
        | **return** list with link_id, shorthash, entry_date and comment
        """
        if not shorthash:
            return None
        try:
            cursor = self._get_connection()[1]
            cursor.execute('''SELECT `block`.`link_id`,
                                     `link`.`link_shorthash`,
                                     `block`.`entry_date`, `comment`
                              FROM `link`, `block`
                              WHERE `link`.`link_shorthash` = %s
                              AND `link`.`link_id` = `block`.`link_id`; ''', (shorthash))
            result = cursor.fetchone()
            cursor.close()
            if result:
                return result
            else:
                return None
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
    #-------------------------------------------------------------------

    def add_logentry_to_database(self, shorthash):
        """
        Creates a log entry inside DB for a given hash.

        | **param** hash (str)
        """
        try:
            conn, cursor = self._get_connection()
            cursor.execute("""INSERT into `access_log` (link_id)
                SELECT link_id
                FROM link
                WHERE link_shorthash = (%s)""",(shorthash))
            conn.commit()
            cursor.close()
        except MySQLdb.DatabaseError:
            pass

    #-------------------------------------------------------------------
    def get_statistics_for_hash(self, shorthash):
        """
        Returns the number of calls for a particular hash

        | **param** hash (str)
        | **return** number of usages (int)
        """
        try:
            conn, cursor = self._get_connection()
            # Is this real a nice way in terms of memory usage at DB?
            cursor.execute("""SELECT count(access_time)
                              FROM access_log left join link on (access_log.link_id = link.link_id)
                              WHERE link.link_shorthash = (%s);""",(shorthash))
            # Is SELECT count(access_time)
            #    FROM access_log, link
            #    WHERE access_log.link_id = link.link_id
            #    AND link.link_shorthash = (%s);
            # maybe better?
            result = cursor.fetchone()
            cursor.close()
            return result[0]
        except MySQLdb.DatabaseError:
            pass
    #-------------------------------------------------------------------
    def get_statistics_for_general_redirects(self, time_range):
        """
        Returns the number of redirects inside a give time range.

        | **param** time_range (str)
        | **return** number of redirects (int)
        """
        queries = ({
            'today'     :   """SELECT CURDATE( ) , count(`access_log_id`)
                            FROM `access_log`
                            WHERE date(`access_time`) = CURDATE( );""",
            'this_year' :   """SELECT COUNT(`access_log_id`)
                            FROM `access_log`
                            WHERE YEAR(`access_time`) = YEAR(CURDATE());""",
            'this_week' :   """SELECT COUNT(`access_log_id`)
                            FROM `access_log`
                            WHERE WEEK(`access_time`) = WEEK(CURDATE());""",
            'this_month':   """SELECT COUNT(`access_log_id`)
                            FROM `access_log`
                            WHERE MONTH(`access_time`) = MONTH(CURDATE());""",
            'per_week'  :   """SELECT YEAR(`access_time`), WEEK(`access_time`),
                            COUNT(`access_log_id`)
                            FROM `access_log`
                            GROUP BY YEAR(`access_time`), WEEK(`access_time`);""",
            'all'       :   """SELECT COUNT(`access_log_id`)
                            FROM `access_log` WHERE 1;"""})
        try:
            conn, cursor = self._get_connection()
            cursor.execute(queries[time_range])
            result = cursor.fetchall()
            cursor.close()
            if time_range == 'per_week':
                return result
            else:
                return result[0]
        except MySQLdb.DatabaseError:
            return None
        except KeyError:
            return None

    #-------------------------------------------------------------------
    def get_statistics_for_general_links(self, time_range):
        """
        Returns the number of added links inside a give time range.

        | **param** time_range (str)
        | **return** number of new links (int)
        """
        queries = ({
            'today'     :   """SELECT CURDATE() , count(`link_id`)
                            FROM `link`
                            WHERE date(`entry_date`) = CURDATE();""",
            'this_year' :   """SELECT count(`link_id`)
                            FROM `link`
                            WHERE YEAR(`entry_date`) = YEAR(CURDATE());""",
            'this_week' :   """SELECT COUNT(`link_id`)
                            FROM `link`
                            WHERE WEEK(`entry_date`) = WEEK(CURDATE());""",
            'this_month' :  """SELECT COUNT(`link_id`)
                            FROM `link`
                            WHERE MONTH(`entry_date`) = MONTH(CURDATE());""",
            'per_week'  :   """SELECT YEAR(`entry_date`), WEEK(`entry_date`),
                            COUNT(`link_id`)
                            FROM `link`
                            GROUP BY YEAR(`entry_date`), WEEK(`entry_date`);""",
            'all'   :       """SELECT COUNT(`link_id`)
                            FROM `link` WHERE 1;"""})
        try:
            conn, cursor = self._get_connection()
            cursor.execute(queries[time_range])
            result = cursor.fetchall()
            cursor.close()
            if time_range == 'per_week':
                return result
            else:
                return result[0]
        except MySQLdb.DatabaseError:
            return None
        except KeyError:
            return None
    #-------------------------------------------------------------------
    def get_date_of_first_entry(self, stats_type, shorthash = None):
        """
        Returns the timestampe of first logged link or redirect

        | **param** stats_type (str)
        | **param** shorthash (str) (only needed in combination with
        |           stats_type == hashredirect
        | **return** timestamp (datetime)
        """
        queries = ({
            'link'          : """SELECT MIN( `entry_date` )
                                 FROM `link`
                                 WHERE `entry_date` > '0000-00-00 00:00:00';""",
            'redirect'      : """SELECT MIN(`access_time`)
                                 FROM `access_log`
                                 WHERE `access_time` > '0000-00-00 00:00:00';""",
            'hashredirect'  : """SELECT MIN(`access_time`)
                                 FROM `access_log`, `link`
                                 WHERE `access_log`.`link_id` = `link`.`link_id`
                                 AND `link`.`link_shorthash` = '%s';"""})
        try:
            conn, cursor = self._get_connection()
            if stats_type == 'hashredirect':
                cursor.execute(queries[stats_type] % shorthash)
            else:
                cursor.execute(queries[stats_type])
            result = cursor.fetchone()
            cursor.close()
            return result
        except MySQLdb.DatabaseError:
            return None
        except KeyError:
            return None
#----------------------------------------------------------------------
    def get_date_of_last_entry(self, stats_type, shorthash = None):
        """
        Returns the timestampe of last logged link or redirect

        | **param** stats_type (str)
        | **param** shorthash (str) (only needed in combination with
        |           stats_type == hashredirect
        | **return** timestamp (datetime)
        """
        queries = ({
            'link'          : """SELECT MAX( `entry_date` )
                                 FROM `link`
                                 WHERE `entry_date` > '0000-00-00 00:00:00';""",
            'redirect'      : """SELECT MAX(`access_time`)
                                 FROM `access_log`
                                 WHERE `access_time` > '0000-00-00 00:00:00';""",
            'hashredirect'  : """SELECT MAX(`access_time`)
                                 FROM `access_log`, `link`
                                 WHERE `access_log`.`link_id` = `link`.`link_id`
                                 AND `link`.`link_shorthash` = '%s';"""})
        try:
            conn, cursor = self._get_connection()
            if stats_type == 'hashredirect':
                cursor.execute(queries[stats_type] % shorthash)
            else:
                cursor.execute(queries[stats_type])
            result = cursor.fetchone()
            cursor.close()
            return result
        except MySQLdb.DatabaseError:
            return None
        except KeyError:
            return None
