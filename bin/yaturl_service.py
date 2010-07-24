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


from yaturl.thread import YuServerThread
from yaturl.server import YuServer
from yaturl.console.manager import ConsoleManager
from ConfigParser import SafeConfigParser
from optparse import OptionParser
from signal import signal, SIGINT, SIGTERM
import daemon
import errno
import logging
import os
import pwd
import sys
from threading import Event


shutdown = Event()


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
def get_error_logger():
    return logging.getLogger('errorlog')


#----------------------------------------------------------------------
def signal_handler(signum, frame):
    """
    On SIGTERM and SIGINT, trigger shutdown
    """
    logger = get_error_logger()
    logger.info(u'Received signal %s, initiating shutdown' % signum)
    shutdown.set()


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
def create_server_threads(config, errorlog, accesslog):

    def set_console_manager_locals():
        locals_ = dict(
            config=config,
            errorlog=errorlog,
            accesslog=accesslog,
            http_server=http_server,
            telnet_server=console_manager.get_telnet_server(),
            console_manager=console_manager)
        console_manager.set_locals(locals_)

    def create_telnet_server():
        if not config.getboolean('telnet', 'enable'):
            return None
        host = config.get('telnet', 'host')
        port = config.getint('telnet', 'port')
        console_manager = ConsoleManager(host, port)
        telnet_server_thread = YuServerThread(
            target=console_manager.serve_forever,
            name='Telnet Console Server',
            instance=console_manager)
        server_threads.append(telnet_server_thread)
        return console_manager

    def create_http_server():
        http_server = YuServer(config, errorlog, accesslog)
        http_server_thread = YuServerThread(
            target=http_server.serve_forever,
            name='HTTP Server',
            instance=http_server)
        server_threads.append(http_server_thread)
        return http_server

    server_threads = []

    http_server = create_http_server()
    console_manager = create_telnet_server()
    set_console_manager_locals()

    return server_threads


#----------------------------------------------------------------------
def watch_running_threads(running_threads, timeout=300):
    # watch running threads
    logger = get_error_logger()
    while not shutdown.isSet():
        for server_thread in running_threads:
            if not server_thread.isAlive():
                logger.error(u'Server thread %s died, shutting down' % server_thread.getName())
                shutdown.set()
        shutdown.wait(timeout)

    # stop remaining threads
    for server_thread in running_threads:
        if server_thread.isAlive():
            server_thread.shutdown()
            server_thread.join()


#----------------------------------------------------------------------
def main():
    """
    main()

    | **return** exit_code (int)
    """

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

    thread_watch_timeout = config.getint('main', 'thread_watch_timeout')

    # (error) logging
    accesslog = setup_logging(config, 'accesslog', '%(message)s')
    errorlog = setup_logging(config, 'errorlog',
        '%(asctime)s: (%(funcName)s():%(lineno)d): %(levelname)s: %(message)s')
    errorlog.info('Application starts up')

    # handle signals
    signal(SIGINT,  signal_handler)
    signal(SIGTERM, signal_handler)

    server_threads = create_server_threads(config, errorlog, accesslog)

    # start server threads
    for server_thread in server_threads:
        server_thread.start()
        errorlog.info('%s started' % server_thread.getName())

    watch_running_threads(server_threads, thread_watch_timeout)

    errorlog.info(u'Shutdown')

    # cleanup
    logging.shutdown()

    return 0


if __name__ == "__main__":
    main()
