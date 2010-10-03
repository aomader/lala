#!/usr/bin/env python
# -*- coding: utf-8 -*-

from anydbm import open as dbopen
from contextlib import closing
from os.path import basename
from signal import signal, SIGQUIT, SIGTERM, SIGINT

from .mpd import MPDThread, mpd_command

class LaLa(object):
    def __init__(self):
        self.read_config()

        self.listener = MPDThread(self.mpd_host, self.mpd_port, self.mpd_pass)
        self.control = MPDThread(self.mpd_host, self.mpd_port, self.mpd_pass)
        self.command = self.control.command

    def start(self):
        signal(SIGQUIT, self.stop)
        signal(SIGTERM, self.stop)
        signal(SIGINT, self.stop)

        self.listener.start()
        self.control.start()

    def stop(self, signum, frame):
        self.listener.stop()
        self.control.stop()

    def read_config(self):
        with closing(dbopen('lala.db', 'c')) as db:
            self.mpd_host = db.get('mpd_host', 'localhost')
            self.mpd_port = db.get('mpd_port', 6600)
            self.mpd_pass = db.get('mpd_pass', None)

    def write_config(self):
        with closing(dbopen('lala.db', 'c')) as db:
            db['mpd_host'] = self.mpd_host
            db['mpd_port'] = self.mpd_port
            db['mpd_pass'] = self.mpd_pass

    def status(self):
        status = self.command('status')
        ret = {'state': status['state']}
        if ret['state'] != 'stop':
            ret['current_song'] = self.current_song(status['time'].split(':')[0])
        return ret

    def current_song(self, time):
        song = self.command('currentsong')
        return {'id': song['id'],
                'name': '%s - %s' % (song['artist'], song['title']),
                'time': self._format_time(time)}
    
    def current_playlist(self):
        return {'tracks': [{'id': song['id'],
                            'title': song['title'],
                            'artist': song['artist'],
                            'time': self._format_time(song['time'])}
                           for song in self.command('playlistinfo')],
                'current': self.command('currentsong').get('id', None)}

    def browse_library(self, path=''):
        return {'items': [{'directory': True,
                           'path': item['directory'],
                           'name': basename(item['directory'])}
                          if item.has_key('directory') else
                          {'directory': False,
                           'path': item['file'],
                           'name': item['artist'] + ' - ' + item['title']}
                          for item in self.command('lsinfo', path)],
                'up': '/'.join(path.split('/')[:-1]) if path != '' else None}
        

    def _format_time(self, time):
        time = int(time)
        return '%i:%02i' % (time / 60, time % 60)
