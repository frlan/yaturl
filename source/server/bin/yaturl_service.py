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


from yaturl import config
from yaturl.console.manager import ConsoleManager
from yaturl.database.database import YuDatabase
from yaturl.helpers.logger import get_access_logger, get_logger
from yaturl.server import YuServer
from yaturl.thread import YuServerThread
from yaturl.constants import TEMPLATENAMES
from optparse import OptionParser
from signal import signal, SIGINT, SIGTERM
import daemon
import errno
import logging
import logging.config
import os
import pwd
import sys
from threading import Event


shutdown_event = Event()


########################################################################
class YuBaseApp(object):
    """Base setups necessary for the service to run"""

    #----------------------------------------------------------------------
    def __init__(self):
        self._access_logger = None
        self._base_dir = None
        self._console_manager = None
        self._http_server = None
        self._logger = None
        self._options = None
        self._pid_file_path = None
        self._server_threads = list()
        self._thread_watchdog_timeout = None

    #----------------------------------------------------------------------
    def setup(self):
        self._setup_basedir()
        self._setup_options()
        self._setup_config()
        self._check_templates()
        self._set_uid()
        self._setup_pidfile_path()
        self._daemonize()
        self._check_already_running()
        self._write_pidfile()
        self._setup_logging()
        self._setup_thread_watchdog()
        self._setup_signal_handler()

    #----------------------------------------------------------------------
    def _setup_basedir(self):
        self._base_dir = os.path.abspath('%s/..' % (os.path.dirname(__file__)))

    #----------------------------------------------------------------------
    def _setup_options(self):
        """
        Set up options and defaults

        @param parser (optparse.OptionParser())
        """
        option_parser = OptionParser()
        option_parser.add_option(
            '-c', dest='config',
            default='%s/etc/yaturl.conf' % self._base_dir,
            help=u'configuration file')

        option_parser.add_option(
            '-f', action='store_false',
            dest='daemonize',
            default=True,
            help=u'stay in foreground, do not daemonize')

        self._options = option_parser.parse_args()[0]

    #----------------------------------------------------------------------
    def _setup_config(self):
        if not os.path.exists(self._options.config):
            raise RuntimeError(u'Configuration file does not exist')
        config.read(self._options.config)

    #----------------------------------------------------------------------
    def _check_templates(self):
        if config.has_option('templates', 'path'):
            for template in TEMPLATENAMES:
                tmp_path = config.get('templates', 'path') + template
                if not os.path.exists(tmp_path):
                    raise RuntimeError(u'Template "%s" not found' % template)

    #----------------------------------------------------------------------
    def _set_uid(self):
        if config.has_option('main', 'user'):
            name = config.get('main', 'user')
            uid = pwd.getpwnam(name)[2]
            os.setuid(uid)

    #----------------------------------------------------------------------
    def _setup_logging(self):
        logging.config.fileConfig(self._options.config)
        self._access_logger = get_access_logger()
        self._logger = get_logger()
        self._logger.info('Application starts up')

    #----------------------------------------------------------------------
    def _daemonize(self):
        if self._options.daemonize:
            # here we fork
            daemon.WORKDIR = self._base_dir
            daemon.createDaemon()

    #----------------------------------------------------------------------
    def _setup_pidfile_path(self):
        self._pid_file_path = config.get('main', 'pid_file_path')

    #----------------------------------------------------------------------
    def _check_already_running(self):
        if self._is_service_running():
            raise RuntimeError(u'Already running')

    #----------------------------------------------------------------------
    def _is_service_running(self):
        """
        Check whether the service is already running
        """
        if os.path.exists(self._pid_file_path):
            pid_file = open(self._pid_file_path, 'r')
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
    def _write_pidfile(self):
        pid = os.getpid()
        pid_file = open(self._pid_file_path, 'w')
        pid_file.write(str(pid))
        pid_file.close()

    #----------------------------------------------------------------------
    def _setup_thread_watchdog(self):
        self._thread_watchdog_timeout = config.getint('main', 'thread_watch_timeout')

    #----------------------------------------------------------------------
    def _setup_signal_handler(self):
        signal(SIGINT,  self._signal_handler)
        signal(SIGTERM, self._signal_handler)

    #----------------------------------------------------------------------
    def _signal_handler(self, signum, frame):
        self._logger.info(u'Received signal %s' % signum)
        self.shutdown()

    #----------------------------------------------------------------------
    def _setup_database(self):
        YuDatabase.init_connection_pool()

    #----------------------------------------------------------------------
    def shutdown(self):
        self._logger.info(u'Initiating shutdown')
        shutdown_event.set()

    #----------------------------------------------------------------------
    def start(self):
        # prepare
        self._create_http_server()
        self._create_telnet_server_if_necessary()
        # here we go
        self._start_server_threads()
        # wait for shutdown
        self._start_thread_watchdog()
        # bye bye
        self._shutdown_logging()

    #----------------------------------------------------------------------
    def _create_http_server(self):
        self._http_server = YuServer(shutdown_event)
        target = self._http_server.serve_forever
        self._create_server_thread(u'HTTP Server', target, self._http_server)

    #----------------------------------------------------------------------
    def _create_server_thread(self, name, target, instance):
        thread = YuServerThread(target=target, name=name, instance=instance)
        # register this thread
        self._server_threads.append(thread)

    #----------------------------------------------------------------------
    def _create_telnet_server_if_necessary(self):
        if config.getboolean('telnet', 'enable'):
            self._create_telnet_server()

    #----------------------------------------------------------------------
    def _create_telnet_server(self):
        self._console_manager = ConsoleManager()
        target = self._console_manager.serve_forever
        self._create_server_thread('Telnet Console Server', target, self._console_manager)
        self._setup_console_manager_locals()

    #----------------------------------------------------------------------
    def _setup_console_manager_locals(self):
        locals_ = dict(
            config=config,
            logger=self._logger,
            accesslog=self._access_logger,
            http_server=self._http_server,
            telnet_server=self._console_manager.get_telnet_server(),
            console_manager=self._console_manager,
            shutdown=self.shutdown,
            get_system_status=ConsoleManager.get_system_status)
        self._console_manager.set_locals(locals_)

    #----------------------------------------------------------------------
    def _start_server_threads(self):
        for server_thread in self._server_threads:
            server_thread.start()

    #----------------------------------------------------------------------
    def _start_thread_watchdog(self):
        """watch running threads, shutdown if there are no more running threads"""
        while not shutdown_event.isSet():
            for server_thread in self._server_threads:
                if not server_thread.isAlive():
                    thread_name = server_thread.getName()
                    self._logger.error(u'Server thread "%s" died, shutting down' % thread_name)
                    shutdown_event.set()
            shutdown_event.wait(self._thread_watchdog_timeout)

        # stop remaining threads
        for server_thread in self._server_threads:
            if server_thread.isAlive():
                server_thread.shutdown()
                server_thread.join()

    #----------------------------------------------------------------------
    def _shutdown_logging(self):
        self._logger.info(u'Shutdown')
        logging.shutdown()


#----------------------------------------------------------------------
def main():
    """
    main()

    | **return** exit_code (int)
    """
    app = YuBaseApp()
    try:
        app.setup()
    except Exception, e:
        print >> sys.stderr, u'Application Setup Error: %s' % unicode(e)
        exit(1)

    try:
        app.start()
    except Exception, e:
        print >> sys.stderr, u'Application Startup Error: %s' % unicode(e)
        exit(1)

    exit(0)


if __name__ == "__main__":
    main()
