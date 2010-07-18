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


from yaturl.server import YuServer
from console import TelnetInteractiveConsoleServer
from ConfigParser import SafeConfigParser
from optparse import OptionParser
from signal import signal, SIGINT, SIGTERM
import daemon
import errno
import logging
import os
import pwd
import sys
import threading


TELNET_CONSOLE_SERVER = None
HTTP_SERVER = None


#----------------------------------------------------------------------
def setup_options(base_dir, parser):
    """
    Set up options and defaults

    @param parser (optparse.OptionParser())
    """
    parser.add_option(
        '-c', dest='config',
        default='%s/etc/yaturl.conf' % base_dir,
        help=u'configuration file')
    parser.add_option(
        '-f', action='store_false',
        dest='daemonize',
        default=True,
        help=u'stay in foreground, do not daemonize')

#----------------------------------------------------------------------
def cleanup():
    if TELNET_CONSOLE_SERVER:
        TELNET_CONSOLE_SERVER.stop()
    logging.shutdown()

#----------------------------------------------------------------------
def signal_handler(signum, frame):
    """
    On SIGTERM and SIGINT, cleanup and exit
    """
    cleanup()
    sys.exit(1)

#----------------------------------------------------------------------
def is_service_running(pid_file_path):
    """
    Check whether the service is already running

    | **param** pid_file_path (str)
    | **return** is_running (bool)
    """
    if os.path.exists(pid_file_path):
        pid_file = open(pid_file_path, 'r')
        pid = pid_file.read().strip()
        pid_file.close()
        if pid:
            try:
                pid = int(pid)
            except ValueError:
                return False
            # sending signal 0 fails if the process doesn't exist (anymore)
            # and won't do anything if the process is running
            try:
                os.kill(pid, 0)
            except OSError, e:
                if e.errno == errno.ESRCH:
                    return False
        return True
    return False

#----------------------------------------------------------------------
def setup_logging(config, name, fmt):
    """
    Set up logging

    | **param** confg (SafeConfigParser)
    | **param** name (str)
    | **param** fmt (str)
    | **return** logger (logging.Logger)
    """
    logger = logging.getLogger(name)
    # TODO maybe use (Timed)RotatingFileHandler
    handler = logging.FileHandler(config.get('main', name))
    formatter = logging.Formatter(fmt)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

    return logger

#----------------------------------------------------------------------
def start_telnet_console(config, _locals):
    global TELNET_CONSOLE_SERVER
    if config.getboolean('telnet', 'enable'):
        # fire up telnet server console
        host = config.get('telnet', 'host')
        port = config.getint('telnet', 'port')
        TELNET_CONSOLE_SERVER = TelnetInteractiveConsoleServer(host=host, port=port, _locals=_locals)
        console_thread = threading.Thread(target=TELNET_CONSOLE_SERVER.accept_interactions)
        console_thread.start()

#----------------------------------------------------------------------
def main():
    """
    main()

    | **return** exit_code (int)
    """
    global HTTP_SERVER

    base_dir = os.path.abspath('%s/..' % (os.path.dirname(__file__)))

    # arguments
    option_parser = OptionParser()
    setup_options(base_dir, option_parser)
    arg_options = option_parser.parse_args()[0]

    # configuration
    config = SafeConfigParser()
    if not os.path.exists(arg_options.config):
        raise RuntimeError(u'Configuration file does not exist')
    config.read(arg_options.config)

    # set uid
    if config.has_option('main', 'user'):
        name = config.get('main', 'user')
        uid = pwd.getpwnam(name)[2]
        os.setuid(uid)

    # daemonize
    if arg_options.daemonize:
        daemon.WORKDIR = base_dir
        daemon.createDaemon()

    # pid handling
    pid_file_path = config.get('main', 'pid_file_path')
    if is_service_running(pid_file_path):
        print >> sys.stderr, 'Already running'
        exit(1)
    pid = open(pid_file_path, 'w')
    pid.write(str(os.getpid()))
    pid.close()

    # (error) logging
    accesslog = setup_logging(config, 'accesslog', '%(message)s')
    errorlog = setup_logging(config, 'errorlog',
        '%(asctime)s: (%(funcName)s():%(lineno)d): %(levelname)s: %(message)s')

    # handle signals
    signal(SIGINT,  signal_handler)
    signal(SIGTERM, signal_handler)

    errorlog.info('Server started')

    server = HTTP_SERVER = YuServer(config, errorlog, accesslog)

    _locals = dict(server=server, config=config, errorlog=errorlog, accesslog=accesslog)
    start_telnet_console(config, _locals)

    # loop forever listening to connections.
    server.serve_forever()

    cleanup()
    exit(0)


if __name__ == "__main__":
    main()
