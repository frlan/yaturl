# -*- coding: utf-8 -*-
#
#       stats.py
#
#       Copyright 2010-2011 Frank Lanitz <frank(at)frank(dot)uvena(dot)de>
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

from yaturl.database.database import YuDatabase
from time import time


class YuStats(object):
    """
    A class to represent some statistic data for yaturl
    """
    def __init__(self):
        self.create_time_stamp = None
        self.links_today = None
        self.links_this_week = None
        self.links_this_month = None
        self.links_this_year = None
        self.links_all = None
        self.redirect_today = None
        self.redirect_this_week = None
        self.redirect_this_month = None
        self.redirect_this_year = None
        self.redirect_per_week = None
        self.redirect_all = None
        self.date_of_first_redirect = None
        self.date_of_first_link = None
        self._db = YuDatabase()
        self._update()

    #-------------------------------------------------------------------
    def _update(self):
        """
        Updates the values of the stats object.
        """
        self.create_time_stamp = time()
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

    #-------------------------------------------------------------------
    def _get_links_from_db_today(self):
        """
        Collecting statistics about links added today from database.
        """
        try:
            return self._db.get_statistics_for_general_links('today')[1]
        except TypeError:
            return None

    #-------------------------------------------------------------------
    def _get_links_from_db_this_week(self):
        """
        Collecting statistics about links added this week from database.
        """
        try:
            return self._db.get_statistics_for_general_links('this_week')[0]
        except TypeError:
            return None

    #-------------------------------------------------------------------
    def _get_links_from_db_this_month(self):
        """
        Collecting statistics about links added this month from database.
        """
        try:
            return self._db.get_statistics_for_general_links('this_month')[0]
        except TypeError:
            return None

    #-------------------------------------------------------------------
    def _get_links_from_db_this_year(self):
        """
        Collecting statistics about links added this year from database.
        """
        try:
            return self._db.get_statistics_for_general_links('this_year')[0]
        except TypeError:
            return None
    #-------------------------------------------------------------------
    def _get_links_from_db_all(self):
        """
        Collecting statistics about links added all time from database.
        """
        try:
            return self._db.get_statistics_for_general_links('all')[0]
        except TypeError:
            return None

    #-------------------------------------------------------------------
    def _get_redirects_today(self):
        """
        Collecting statistics about done redirects of today from database.
        """
        try:
            return self._db.get_statistics_for_general_redirects('today')[1]
        except TypeError:
            return None

    #-------------------------------------------------------------------
    def _get_redirects_this_week(self):
        """
        Collecting statistics about done redirects of this week from database.
        """
        try:
            return self._db.get_statistics_for_general_redirects('this_week')[0]
        except TypeError:
            return None

    #-------------------------------------------------------------------
    def _get_redirects_this_month(self):
        """
        Collecting statistics about done redirects of this month from database.
        """
        try:
            return self._db.get_statistics_for_general_redirects('this_month')[0]
        except TypeError:
            return None

    #-------------------------------------------------------------------
    def _get_redirects_this_year(self):
        """
        Collecting statistics about done redirects of this year from database.
        """
        try:
            return self._db.get_statistics_for_general_redirects('this_year')[0]
        except TypeError:
            return None

    #-------------------------------------------------------------------
    def _get_redirects_per_week(self):
        """
        Collecting statistics about done redirects groupd by week and year
        from database.
        """
        try:
            return self._db.get_statistics_for_general_redirects('per_week')
        except TypeError:
            return None

    #-------------------------------------------------------------------
    def _get_redirects_all(self):
        """
        Collecting statistics about done redirects ever from database.
        """
        try:
            return self._db.get_statistics_for_general_redirects('all')[0]
        except TypeError:
            return None

    #-------------------------------------------------------------------
    def _get_date_of_first_redirect(self):
        """
        Get timestamp of first redirect logged from database.
        """
        try:
            return self._db.get_date_of_first_entry('redirect')[0]
        except TypeError:
            return None

    #-------------------------------------------------------------------
    def _get_date_of_first_link_entry(self):
        """
        Get timestamp of time of first inserted link from database.
        """
        try:
            return self._db.get_date_of_first_entry('link')[0]
        except TypeError:
            return None

    #-------------------------------------------------------------------
    def update_stats(self):
        """
        Public method to perform update on stats date
        """
        self._update()
