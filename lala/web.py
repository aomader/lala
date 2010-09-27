#!/usr/bin/env python
# -*- coding: utf-8 -*-

from operator import itemgetter

from flask import Flask, render_template, jsonify, request

from .mpd import MPDThread, NotConnected, mpd_command
from .app import LaLa

app = Flask(__name__)
lala = LaLa()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/status')
@mpd_command
def api_status():
    return lala.status()

@app.route('/api/control/<action>')
@mpd_command
def api_control(action):
    if action not in ('play', 'stop', 'pause', 'next', 'previous'):
        return ''

    lala.command(action)
    return lala.status()

@app.route('/api/playlist/info')
@mpd_command
def api_playlist_info():
    return lala.current_playlist()

@app.route('/api/library')
@mpd_command
def api_library():
    return lala.browse_library(request.args.get('path', ''))

def run():
    lala.start()
    app.run(host='0.0.0.0', debug=True, use_reloader=False, processes=1)
