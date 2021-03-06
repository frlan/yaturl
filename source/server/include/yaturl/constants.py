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


SERVER_NAME = u'yatURL.net'
SERVER_VERSION = u'1.0'

TEMPLATENAMES = ['404', '500', 'contactUsResult', 'databaseerror',
'homepage', 'return', 'showpage', 'stats', 'statsLink']

CONTENT_TYPES = ({
    '.css': 'text/css',
    '.ico': 'image/vnd.microsoft.icon',
    '.png': 'image/png'
})

# we need to hard-code this one at least in case of the file cannot be found on disk
TEMPLATE_500 = '''<!DOCTYPE html>
<html lang="en">

<head>
    <title>yatURL.net - Internal server error</title>
    <meta charset="utf-8" />
    <meta name="generator" content="Geany 0.19.1" />
    <link rel="stylesheet" href="/default.css" />
    <link rel="shortcut icon" href="/favicon.ico" />
</head>

<body>
    <p>500 - Internal server error</p>

    <p>The server encountered an internal error and was unable to complete your request.</p>
</body>
</html>
'''


FOOTER = '''
            <div id="footer"><span><a href="/ContactUs">Contact Us</a>
            <a href="/About">About</a>
            <a href="/faq">F.A.Q.</a>
            <a href="/stats">Stats</a>
            <a href="/">Home</a></span></div>
    </div>
</body>
</html>'''


HEADER = '''<!DOCTYPE html>
<html lang="en">

<head>
    <title>%s</title>
    <meta charset="utf-8" />
    <meta name="generator" content="Geany 0.19.1" />
    <link rel="stylesheet" href="/default.css" />
    <link rel="shortcut icon" href="/favicon.ico" />
</head>

<body>
    <div id="container">
        <div id="header"><span>%s</span></div>
'''
