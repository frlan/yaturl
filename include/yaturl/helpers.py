#!/usr/bin/env python
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


import os


#----------------------------------------------------------------------
def sanitize_path(path):
    """
    Check whether the given path is valid and remove any '..'

    @param path (str) - the path to check
    @return the full normalized absolute path (str)
    """
    if not path:
        return ''
    if os.path.isabs(path):
        # skip leading slashes
        path = path[1:]
    # drop query string
    query_string_start = path.find('?')
    if query_string_start > -1:
        path = path[0:query_string_start]
    # sanitize path
    return os.path.normpath(path)

