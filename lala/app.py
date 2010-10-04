#!/usr/bin/env python
# -*- coding: utf-8 -*-

from anydbm import open as dbopen
from contextlib import closing
from os.path import basename
from signal import signal, SIGQUIT, SIGTERM, SIGINT

from .mpd import MPDThread, mpd_command

class LaLa(object):
    def start(self, host, port, password):
        signal(SIGQUIT, self.stop)
        signal(SIGTERM, self.stop)
        signal(SIGINT, self.stop)

        self.listener = MPDThread(host, port, password, True)
        self.control = MPDThread(host, port, password)
        self.command = self.control.command

        self.listener.start()
        self.control.start()

    def stop(self, signum, frame):
        self.listener.stop()
        self.control.stop()
    '''
    def read_config(self):
        with closing(dbopen('lala.db', 'c')) as db:
            self.mpd_host = db.get('mpd_host', 'localhost')
            self.mpd_port = int(db.get('mpd_port', 6600))
            self.mpd_pass = db.get('mpd_pass', None)

    def write_config(self):
        with closing(dbopen('lala.db', 'c')) as db:
            db['mpd_host'] = self.listener.host = self.control.host = self.mpd_host
            db['mpd_port'] = self.listener.port = self.control.port = self.mpd_port
            db['mpd_pass'] = self.listener.password = self.control.password = self.mpd_pass
    '''
    def status(self):
        status = self.command('status')
        ret = {'state': status['state']}
        up = []
        while not self.listener.updates.empty():
            up += self.listener.updates.get_nowait()
        if up:
            ret['updates'] = up
        if ret['state'] != 'stop':
            ret['current_song'] = self.current_song(status['time'].split(':')[0])
        return ret

    def current_song(self, time):
        song = self.command('currentsong')
        return {'id': song['id'],
                'name': '%s - %s' % (song['artist'], song['title']),
                'time': self.format_time(time)}

    def format_time(self, time):
        time = int(time)
        return '%i:%02i' % (time / 60, time % 60)
