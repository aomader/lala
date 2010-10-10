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

from json import dumps, load
from os import path

from twisted.internet.defer import inlineCallbacks, returnValue
from twisted.web.resource import Resource, NoResource
from twisted.web.server import NOT_DONE_YET

from mpd import CommandError, CommandListError

# show status information
@inlineCallbacks
def status(lala, request):
    status = yield lala.status()
    returnValue(status)

# control
@inlineCallbacks
def control_play(lala, request):
    result = yield lala.command('play')
    returnValue(lala.status())

@inlineCallbacks
def control_pause(lala, request):
    result = yield lala.command('pause', 1)
    returnValue(lala.status())

@inlineCallbacks
def control_stop(lala, request):
    result = yield lala.command('stop')
    returnValue(lala.status())

@inlineCallbacks
def control_previous(lala, request):
    result = yield lala.command('previous')
    returnValue(lala.status())

@inlineCallbacks
def control_next(lala, request):
    result = yield lala.command('next')
    returnValue(lala.status())

# current playlist operations
@inlineCallbacks
def current_list(lala, request):
    tracks = yield lala.command('playlistinfo')
    returnValue({'tracks':
        [{'id': track['id'],
          'file': track['file'],
          'artist': track['artist'],
          'title': track['title'],
          'time': track['time']}
         for track in tracks]})

@inlineCallbacks
def current_play(lala, request):
    result = yield lala.command('playid', int(request.json['track']))
    returnValue(lala.status())

@inlineCallbacks
def current_add(lala, request):
    result = yield lala.command([('add', path) for path in request.json['paths']])
    returnValue(lala.status())

@inlineCallbacks
def current_delete(lala, request):
    result = yield lala.command([('deleteid', int(track)) for track in request.json['tracks']])
    returnValue(lala.status())

@inlineCallbacks
def current_clear(lala, request):
    result = yield lala.command('clear')
    returnValue(lala.status())

# library operations
@inlineCallbacks
def library_list(lala, request):
    opath = request.json['path'] if 'path' in request.json else ''
    result = yield lala.command('lsinfo', opath)

    ret = {'paths':
        [{'directory': True if 'directory' in item else False,
          'path': item['directory'] if 'directory' in item else item['file'],
          'name': path.basename(item['directory']) if 'directory' in item else item['artist'] + ' - ' + item['title']}
         for item in result]}
    if opath != '':
        ret['up'] = '/'.join(opath.split('/')[:-1])

    returnValue(ret)

@inlineCallbacks
def library_update(lala, request):
    result = yield lala.command([('update', path) for path in request.json['paths']])


ROUTES = [
    ('status', status),

    ('control/play', control_play),
    ('control/pause', control_pause),
    ('control/stop', control_stop),
    ('control/previous', control_previous),
    ('control/next', control_next),

    ('current/list', current_list),
    ('current/play', current_play),
    ('current/add', current_add),
    ('current/delete', current_delete),
    ('current/clear', current_clear),

    ('library/list', library_list),
    ('library/update', library_update),
]


class API(Resource):
    isLeaf = True

    def __init__(self, lala):
        Resource.__init__(self)
        self.lala = lala

    def render_POST(self, request):
        for url, function in ROUTES:
            if '/api/' + url == request.path:
                request.setHeader('Content-Type', 'application/json')
                try:
                    request.json = load(request.content)
                except ValueError:
                    request.json = None
                a = function(self.lala, request)
                a.addCallback(self.success, request)
                a.addErrback(self.error, request)
                return NOT_DONE_YET
        return 'LORN %s' % request.URLPath()

    def success(self, result, request):
        request.write(dumps({'status': 'ok', 'data': result}))
        request.finish()

    def error(self, failure, request):
        failure.trap(CommandError, CommandListError)
        request.write(dumps({'status': 'error', 'reason':
                             failure.getErrorMessage()}))
        request.finish()
