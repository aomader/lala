#!/usr/bin/env python
# -*- coding: utf-8 -*-

from base64 import b16encode, b16decode
from operator import itemgetter
from os.path import basename
from urllib import quote, unquote

from flask import Flask, render_template, jsonify, request, abort

from .mpd import MPDThread, NotConnected, mpd_command
from .app import LaLa

app = Flask(__name__)
lala = LaLa()

# base16 conversions
b16in = lambda encoded: b16decode(encoded).decode('utf-8')
b16out = lambda decoded: b16encode(decoded.encode('utf-8'))

# url escaping
urlout = lambda url: quote(url.encode('utf-8'))
urlin = lambda url: unquote(url.encode('utf-8')).decode('utf-8')

# template filter
@app.template_filter('duration')
def duration(value):
    return lala.format_time(value)

@app.template_filter('base16')
def base16(value):
    return b16out(value)

@app.template_filter('url')
def url(value):
    return urlout(value)

# deliver the main pages
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if request.method == 'POST':
        '''
        lala.mpd_host = request.json['host']
        lala.mpd_port = int(request.json['port'])
        lala.mpd_pass = request.json['pass']
        lala.write_config()
        '''
        return 'OK'
    else:
        return render_template('settings.html', mpd_host=lala.mpd_host,
            mpd_port=lala.mpd_port, mpd_pass=lala.mpd_pass)

# the api calls
@app.route('/api/status', methods=['POST'])
@mpd_command
def api_status():
    return lala.status()

@app.route('/api/control/<action>', methods=['POST'])
@mpd_command
def api_control(action):
    if action not in ('play', 'stop', 'pause', 'next', 'previous'):
        abort(400)
    lala.command(action)
    return lala.status()

@app.route('/api/current/<action>', methods=['POST'])
@mpd_command
def api_current(action):
    if action == 'list':
        return render_template('list_current.html', tracks=lala.command('playlistinfo'))
    elif action == 'play':
        lala.command('playid', int(request.json['track']))
        return lala.status()
    elif action == 'add':
        if request.json.get('replace', False):
            lala.command('clear')
        for path in request.json['paths']:
            lala.command('add', b16in(path).encode('utf-8'))
    elif action == 'delete':
        for track in request.json['tracks']:
            lala.command('deleteid', int(track))
    elif action == 'clear':
        lala.command('clear')
    else:
        abort(400)
    return None

@app.route('/api/library/<action>', methods=['POST'])
@mpd_command
def api_library(action):
    if action == 'list':
        path = b16in(request.json['expand']) if 'expand' in request.json else urlin(request.json.get('path', ''))
        level = int(request.json.get('level', 0))
        return render_template('list_library.html', items=lala.command('lsinfo', path.encode('utf-8')),
            level=level, current_path=path, up='/'.join(path.split('/')[:-1]) if path != '' else None)
    elif action == 'update':
        for path in request.json['paths']:
            lala.command('update', b16in(path).encode('utf-8'))
    else:
        abort(400)
    return None

def run(host, port, password):
    lala.start(host, port, password)
    app.run(host='0.0.0.0', debug=False, use_reloader=False, processes=1)

