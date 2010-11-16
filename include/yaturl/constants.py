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



SERVER_NAME = 'yatURL.net'
SERVER_VERSION = '1.0'
MYSQL_CONNECTION_POOL_SIZE = 5


# we need to hard-code this one at least in case of the file cannot be found on disk
TEMPLATE_500 = '''<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
  "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">

<head>
    <title>yatURL.net - Internal server error</title>
    <meta http-equiv="content-type" content="text/html;charset=utf-8" />
    <meta name="generator" content="Geany 0.19.1" />
</head>

<body>
    <p>500 - Internal server error</p>

    <p>The server encountered an internal error and was unable to complete your request.</p>
</body>
</html>
'''


FOOTER = '''\
            <div id="footer"><span><a href="/ContactUs">Contact Us</a> &nbsp;&nbsp; <a href="/About">About</a> &nbsp;&nbsp; <a href="/">Home</a> </span></div>
    </div>
</body>
</html>'''


HEADER = '''\
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
    "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">

<head>
    <title>%s</title>
    <meta http-equiv="content-type" content="text/html;charset=utf-8" />
    <meta name="generator" content="Geany 0.19.1" />
    <link rel="stylesheet" href="/default.css" type="text/css"/>
</head>

<body>
    <div id="container">
        <div id="header"><span>%s</span></div>
'''
