# -*- coding: utf-8 -*-
#
#       stats.py
#
#       Copyright 2010 Frank Lanitz <frank(at)frank(dot)uvena(dot)de>
#
#       This program is free software; you can redistribute it and/or modify
#       it under the terms of the GNU General Public License as published by
#       the Free Software Foundation; either version 2 of the License, or
#       (at your option) any later version.
#
#       This program is distributed in the hope that it will be useful,
#       but WITHOUT ANY WARRANTY; without even the implied warranty of
#       MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#       GNU General Public License for more details.
#
#       You should have received a copy of the GNU General Public License
#       along with this program; if not, write to the Free Software
#       Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#       MA 02110-1301, USA.

from yaturl.db import YuDbError, YuDb
from yaturl.constants import SERVER_NAME, SERVER_VERSION
import time

class YuStats:
    def __init__(self, server):
        self._db = YuDb(server.config, server.errorlog)
        self.create_time_stamp = time.clock()
        self.links_today = self._get_links_from_db_today()
        self.links_this_week = self._get_links_from_db_this_week()
        self.links_this_month = self._get_links_from_db_this_month()
        self.links_this_year = self._get_links_from_db_this_year()
        self.links_all = self._get_links_from_db_all()
        self.redirect_today = self._get_redirects_today()
        self.redirect_this_week = self._get_redirects_this_week()
        self.redirect_this_month = self._get_redirects_this_month()
        self.redirect_this_year = self._get_redirects_this_year()
        # self.redirect_per_week = self._get_redirects_per_week()
        self.redirect_all = self._get_redirects_all()
        self.date_of_first_redirect = self._get_date_of_first_redirect()
        self.date_of_first_link = self._get_date_of_first_link_entry()

    def _update(self):
        # Not sure whether this is a nice way on doing this
        self.__init__()

    def _get_links_from_db_today(self):
        return self._db.get_statistics_for_general_links('today')[1]

    def _get_links_from_db_this_week(self):
        return self._db.get_statistics_for_general_links('this_week')[0]

    def _get_links_from_db_this_month(self):
        return self._db.get_statistics_for_general_links('this_month')[0]

    def _get_links_from_db_this_year(self):
        return self._db.get_statistics_for_general_links('this_year')[0]

    def _get_links_from_db_all(self):
        return self._db.get_statistics_for_general_links('all')[0]

    def _get_redirects_today(self):
        return self._db.get_statistics_for_general_redirects('today')[1]

    def _get_redirects_this_week(self):
        return self._db.get_statistics_for_general_redirects('this_week')[0]

    def _get_redirects_this_month(self):
        return self._db.get_statistics_for_general_redirects('this_month')[0]

    def _get_redirects_this_year(self):
        return self._db.get_statistics_for_general_redirects('this_year')[0]

    def _get_redirects_per_week(self):
        return self._db.get_statistics_for_general_redirects('per_week')


    def _get_redirects_all(self):
        return self._db.get_statistics_for_general_redirects('all')[0]

    def _get_date_of_first_redirect(self):
        return self._db.get_date_of_first_entry('redirect')[0]

    def _get_date_of_first_link_entry(self):
        return self._db.get_date_of_first_entry('link')[0]
