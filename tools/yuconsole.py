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



from telnetlib import Telnet
import __main__
import readline
import rlcompleter
import sys

TELNET_TIMEOUT = 30


########################################################################
class TelnetClient(object):

    #----------------------------------------------------------------------
    def __init__(self, host, port):
        self._client = Telnet(host, port, timeout=TELNET_TIMEOUT)
        self._prompts = dict(default='>>> ', continous='... ')
        self._prompt_default = self._prompts['default']
        self._prompt_continous = self._prompts['continous']
        self._next_prompt = self._prompts['default']

    #----------------------------------------------------------------------
    def _read_input(self):
        prompt = self._next_prompt if sys.stdin.isatty() else ''
        data_to_send = str(raw_input(prompt))
        data_to_send += '\n'
        return data_to_send

    #----------------------------------------------------------------------
    def _read_response(self):
        return self._client.read_eager()

    #----------------------------------------------------------------------
    def _get_next_prompt(self, response):
        current_prompt = response[-4:]
        if current_prompt in self._prompts.itervalues():
            self._next_prompt = current_prompt
        else:
            self._next_prompt = None

    #----------------------------------------------------------------------
    def _have_prompt(self):
        return (self._next_prompt is not None)

    #----------------------------------------------------------------------
    def _fetch_remote_locals(self):
        """
        Read the locals() from the remote console and then add their keys
        into the local main namespace to get them auto completed as they were
        'real' locals.
        """
        self._client.write('locals().keys()\n')
        received_data = self._client.read_until(self._prompt_default, timeout=TELNET_TIMEOUT)
        received_data = received_data[:-4]
        keys = eval(received_data)
        for key in keys:
            if not __main__.__dict__.has_key(key):
                __main__.__dict__[key] = getattr(__main__, key, None)

    #----------------------------------------------------------------------
    def _get_initial_prompt(self):
        received_data = self._client.read_until(self._prompt_default, timeout=TELNET_TIMEOUT)
        if sys.stdin.isatty():
            sys.stdout.write(received_data[:-4])
            # do some magic for auto completion
            self._fetch_remote_locals()
            # enable readline completion after we filled __main__.__dict__ with the
            # locals of the remote console
            readline.parse_and_bind("tab: complete")

    #----------------------------------------------------------------------
    def _run(self):
        self._get_initial_prompt()
        while True:
            if self._have_prompt():
                data_to_send = self._read_input()
                if data_to_send:
                    self._client.write(data_to_send)

            received_data = self._read_response()
            self._get_next_prompt(received_data)
            if self._next_prompt:
                # cut off the prompt, if any
                received_data = received_data[:-4]
            # print data
            sys.stdout.write(received_data)

    #----------------------------------------------------------------------
    def run(self):
        try:
            return self._run()
        except (EOFError, KeyboardInterrupt):
            pass
        finally:
            self._client.close()


#----------------------------------------------------------------------
def main():
    host = '127.0.0.1'
    port = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1] else 24883

    telnet_client = TelnetClient(host, port)
    telnet_client.run()

    return 0


if __name__ == '__main__':
    main()
