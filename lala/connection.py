#!/usr/bin/env python
# -*- coding: utf-8 -*-

from functools import wraps
from threading import Thread, Event, Lock, Condition
from time import time, sleep

from flask import jsonify
from mpd import MPDClient, CommandError

class NotConnected(Exception):
    pass

class MPDThread(Thread):
    CONNECTED = 'connected'
    DISCONNECTED = 'disconnected'

    def __init__(self, host='127.0.0.1', port=6600, password=None):
        Thread.__init__(self)

        self.host = host
        self.port = port
        self.password = password

        self._loop = Event()
        self._lock = Lock()
        self._condition = Condition()
        self._mpd = None
        self.status = self.DISCONNECTED
        self.last_error = ''
        self.latency = 0.0
        self.connected_since = 0
        
        self.retry_timeout = 5
        self.idle_timeout = 15

        self._loop.set()

    def run(self):
        while self._loop.is_set():
            if self.status is self.DISCONNECTED:
                if not self._connect():
                    sleep(self.retry_timeout)
                continue

            sleep(self.idle_timeout if self._ping() else self.retry_timeout)

    def command(self, command, *args):
        with self._lock:
            if self.status is self.DISCONNECTED:
                raise NotConnected(self.last_error)

            try:
                return getattr(self._mpd, command)(*args)
            except CommandError as e:
                print 'Unknown command %s: %s' % (command, e)
            except Exception as e:
                self.status = self.DISCONNECTED
                self.last_error = unicode(e)
                raise NotConnected(self.last_error)
                

    def listen(self, callback_func):
        pass

    def get_status(self):
        return {'status': self.status,
                'last_error': self.last_error,
                'latency': self.latency,
                'connected': self.connected_since}

    def stop(self):
        self._loop.clear()
        self.join()

    def _connect(self):
        with self._lock:
            try:
                self._mpd.disconnect()
            except:
                pass
            self._mpd = MPDClient()
            try:
                self._mpd.connect(self.host, self.port)
                if self.password:
                    self._mpd.password(self.password)
                
                self.status = self.CONNECTED
                self.connected_since = time()

                return True
            except Exception as e:
                self.last_error = unicode(e)

        return False

    def _ping(self):
        with self._lock:
            try:
                start = time()
                self._mpd.ping()
                end = time()
                self.latency = round((end - start) * 1000.0, 2)

                return True
            except Exception as e:
                self.status = self.DISCONNECTED
                self.last_error = unicode(e)

        return False
        
def mpd_command(function):
    @wraps(function)
    def decorated_function(*args, **kwargs):
        try:
            return jsonify({'status': 'ok',
                            'data': function(*args, **kwargs)})
        except NotConnected as e:
            return jsonify({'status': 'disconnected',
                            'reason': '%s' % e})
    return decorated_function
