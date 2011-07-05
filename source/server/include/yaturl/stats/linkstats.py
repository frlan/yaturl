# -*- coding: utf-8 -*-
#
#       linkstats.py
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

class YuLinkStats(object):
    """
    Class to represent the link specific stats
    """
    def __init__(self, shorthash):
        self._db = YuDatabase()
        if shorthash is not None and self._db is not None:
            link_details = self._db.get_link_details(shorthash)
            if link_details:
                if link_details[5]:
                    self.creation_time = '%s (UTC)' % (link_details[5])
                else:
                    self.creation_time = 'Unknown'
                self.link_address = link_details[3]
                self.first_redirect = self._db.get_date_of_first_entry('hashredirect', shorthash)[0]
                self.last_redirect = self._db.get_date_of_last_entry('hashredirect', shorthash)[0]
                self.number_of_redirects = self._db.get_statistics_for_hash(shorthash)
                return
        self.link_address = None
        self.creation_time = None
        self.first_redirect = None
        self.last_redirect = None
        self.number_of_redirects = None
