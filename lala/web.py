#!/usr/bin/env python
# -*- coding: utf-8 -*-

from operator import itemgetter

from flask import Flask, render_template, jsonify

from .connection import MPDThread, NotConnected, mpd_command
from .server import LaLa

app = Flask(__name__)
lala = LaLa()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/<command>')
@mpd_command
def api_command(command):
    if command in ('play', 'stop', 'pause', 'next', 'previous'):
        return lala.command(command)
    elif command == 'status':
        status = lala.status()
        status.update(currentsong=lala.command('currentsong'))
        if status['status'] == MPDThread.DISCONNECTED:
            raise NotConnected
        return status
    elif command == 'current':
        tracks = []
        for track in lala.command('playlistinfo'):
            tracks.append({'id': track['id'],
                           'artist': track['artist'],
                           'album': track['album'],
                           'title': track['title'],
                           'time': '%i:%02i' % (int(track['time']) / 60, int(track['time']) % 60)})
        return {'tracks': tracks, 'current': lala.command('currentsong')['id']}

def run():
    lala.start()
    app.run(host='0.0.0.0', debug=True, use_reloader=False, processes=1)
