#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from functools import wraps
from Queue import Queue
from threading import Thread, Event, Lock
from time import time, sleep

from flask import jsonify
from .jat_mpd import MPDClient, MPDError, ConnectionError

class NotConnected(Exception):
    pass
class CommandError(Exception):
    pass

class MPDThread(Thread):
    CONNECTED = 'connected'
    DISCONNECTED = 'disconnected'

    def __init__(self, host='127.0.0.1', port=6600, password=None, update_mode=False):
        Thread.__init__(self)

        self.host = host
        self.port = port
        self.password = password

        self._stop = Event()
        self._lock = Lock()
        self._mpd = None
        self._listen = update_mode
        self.status = self.DISCONNECTED
        self.last_error = ''
        self.latency = 0.0
        self.connected_since = 0
        self.updates = Queue(10)
        
        self.retry_timeout = 5
        self.idle_timeout = 15

    def run(self):
        while not self._stop.is_set():
            if self.status is self.DISCONNECTED:
                if not self._connect():
                    self._stop.wait(self.retry_timeout)
                continue

            if self._listen:
                self._idle()
            else:
                self._stop.wait(self.idle_timeout if self._ping() else self.retry_timeout)

        try:
            self._mpd.close()
            self._mpd.disconnect()
        except:
            pass

    def command(self, command, *args):
        with self._lock:
            if self.status is self.DISCONNECTED:
                raise NotConnected(self.last_error)

            try:
                return getattr(self._mpd, command)(*args)
            except (ConnectionError, IOError) as e:
                self.status = self.DISCONNECTED
                self.last_error = unicode(e)
                raise NotConnected(self.last_error)
            except MPDError as e:
                raise CommandError(unicode(e))

    def stop(self):
        self._stop.set()
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
            except (ConnectionError, IOError) as e:
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
            except (ConnectionError, IOError) as e:
                self.status = self.DISCONNECTED
                self.last_error = unicode(e)

        return False

    def _idle(self):
        with self._lock:
            try:
                up = self._mpd.idle()
                if self.updates.full():
                    try:
                        elf.updates.get_nowait()
                    except Empty:
                        pass
                self.updates.put_nowait(up)
            except (ConnectionError, IOError) as e:
                self.status = self.DISCONNECTED
                self.last_error = unicode(e)
        
def mpd_command(function):
    @wraps(function)
    def decorated_function(*args, **kwargs):
        try:
            return jsonify({'status': 'ok',
                            'data': function(*args, **kwargs)})
        except CommandError as e:
            return jsonify({'status': 'error',
                            'reason': unicode(e)})
        except NotConnected as e:
            return jsonify({'status': 'disconnected',
                            'reason': '%s' % e})
    return decorated_function
