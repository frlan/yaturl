#!/usr/bin/env python
# -*- coding: utf-8 -*-


from yaturl.server import YuServer
from ConfigParser import SafeConfigParser
from optparse import OptionParser
from signal import signal, SIGINT, SIGTERM
import daemon
import errno
import logging
import os
import pwd
import sys

base_dir = os.path.abspath('%s/..' % (os.path.dirname(__file__)))

#----------------------------------------------------------------------
def setup_options(parser):
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
def signal_handler(signum, frame):
    logging.shutdown()
    sys.exit(1)

#----------------------------------------------------------------------
def is_service_running(pid_file_path):
    if os.path.exists(pid_file_path):
        f = open(pid_file_path, 'r')
        pid = f.read().strip()
        f.close()
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
    logger = logging.getLogger(name)
    # TODO maybe use (Timed)RotatingFileHandler
    handler = logging.FileHandler(config.get('main', name))
    formatter = logging.Formatter(fmt)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

    return logger

#----------------------------------------------------------------------
def main():
    # arguments
    option_parser = OptionParser()
    setup_options(option_parser)
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
    # TODO write a formatter for access log
    accesslog = setup_logging(config, 'accesslog',
        '%(asctime)s: %(message)s')
    errorlog = setup_logging(config, 'errorlog',
        '%(asctime)s: %(process)d: (%(funcName)s():%(lineno)d): %(levelname)s: %(message)s')

    # handle signals
    signal(SIGINT,  signal_handler)
    signal(SIGTERM, signal_handler)

    # loop forever listening to connections.
    sc = YuServer(config, errorlog, accesslog)
    sc.serve_forever()

    # clean up though we usually won't get here
    logging.shutdown()
    exit(0)


if __name__ == "__main__":
    main()
