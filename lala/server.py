#!/usr/bin/env python
# -*- coding: utf-8 -*-

from anydbm import open as dbopen
from contextlib import closing
from signal import signal, SIGQUIT, SIGTERM, SIGINT

from .connection import MPDThread

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
        print 'i catched that shit'
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
        return self.control.get_status()
