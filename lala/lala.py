#!/usr/bin/env python

# Copyright (C) 2010  Oliver Mader <b52@reaktor42.de>
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

from twisted.internet.defer import inlineCallbacks

from mpd import MPDFactory, CommandError


class LaLa(object):
    def __init__(self, reactor):
        self.reactor = reactor
        self._ctrl = None
        self._idle = None

        self.state = 'stop'
        self.current_song_id = -1
        self.current_song_title = ''
        self.current_song_pos = 0
        self.current_song_updated = 0
        self.updates = []
        
        ctrl_factory = MPDFactory()
        ctrl_factory.connectionMade = self._ctrl_connection_made
        ctrl_factory.connectionLost = self._ctrl_connection_lost
        reactor.connectTCP('192.168.42.10', 6600, ctrl_factory)

        idle_factory = MPDFactory()
        idle_factory.connectionMade = self._idle_connection_made
        idle_factory.connectionLost = self._idle_connection_lost
        reactor.connectTCP('192.168.42.10', 6600, idle_factory)

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
        updates = list(updates)
        self.updates += updates
        print 'update: %s' % updates
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
            self.current_song_title = song['artist'] + ' - ' + song['title']
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
