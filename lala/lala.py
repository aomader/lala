#!/usr/bin/env python

# Copyright (C) 2010,2011  Oliver Mader <b52@reaktor42.de>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

from time import time

from mpd import MPDFactory, CommandError
from twisted.internet import reactor
from twisted.internet.defer import inlineCallbacks

class NotConnected(Exception):
    pass

class LaLa(object):
    def __init__(self):
        self.disconnect()

    def connect(self, host='127.0.0.1', port=6600, password=None):
        self._ctrl_factory = MPDFactory()
        self._ctrl_factory.connectionMade = self._ctrl_connection_made
        self._ctrl_factory.connectionLost = self._ctrl_connection_lost
        self._ctrl_connector = reactor.connectTCP(host, port,
            self._ctrl_factory)

        self._idle_factory = MPDFactory()
        self._idle_factory.connectionMade = self._idle_connection_made
        self._idle_factory.connectionLost = self._idle_connection_lost
        self._idle_connector = reactor.connectTCP(host, port,
            self._idle_factory)

    def disconnect(self):
        self._ctrl = None
        self._ctrl_factory = None
        self._ctrl_connector = None
        self._idle = None
        self._idle_factory = None
        self._idle_connector = None

        self.state = 'stop'
        self.current_song_id = -1
        self.current_song_title = ''
        self.current_song_pos = 0
        self.current_song_updated = 0
        self.updates = set()
        
    def _ctrl_connection_made(self, connector):
        self._ctrl = connector
        self._update_status()

    def _ctrl_connection_lost(self, connector, reason):
        self._ctrl = None

    def _idle_connection_made(self, connector):
        self._idle = connector
        self._idle.idle().addCallback(self._idle_callback)

    def _idle_connection_lost(self, connector, reason):
        self._idle = None

    def _idle_callback(self, updates):
        self._idle.idle().addCallback(self._idle_callback)

        self.updates.update(updates)
        updates = list(updates)

        if 'player' in updates or 'playlist' in updates:
            self._update_status()

    @inlineCallbacks
    def _update_status(self):
        status = yield self._ctrl.status()
        if status['state'] == 'stop' and self.state != status['state']:
            self.current_song_id = -1
            self.state = 'stop'
        elif status['state'] != 'stop' and status['songid'] != self.current_song_id:
            song = yield self._ctrl.currentsong()
            self.current_song_id = song['id']
            self.current_song_title = song.get('artist', 'Unknown') + ' - ' + song.get('title', 'Unknown')
            self.current_song_pos = int(status['time'].split(':')[0])
            self.current_song_updated = time()
            self.state = status['state']

    def status(self):
        ret = {'state': self.state, 'updates': self.updates}
        self.updates = []
        if self.current_song_id != -1:
            ret['current_song'] = {
                'id': self.current_song_id,
                'title': self.current_song_title,
                'time': int(self.current_song_pos + (time() - self.current_song_updated)) + 1
            }
        return ret

    def command(self, *args):
        if self._ctrl is None:
            raise NotConnected

        if isinstance(args[0], list):
            if len(args[0]) > 1:
                self._ctrl.command_list_ok_begin()
                for params in args[0]:
                    getattr(self._ctrl, params[0])(*params[1:])
                return self._ctrl.command_list_end()
            else:
                return getattr(self._ctrl, args[0][0][0])(*args[0][0][1:])
        else:
            return getattr(self._ctrl, args[0])(*args[1:])
