#!/usr/bin/env python
# -*- coding: utf-8 -*-

from optparse import OptionParser

from .web import run

if __name__ == '__main__':
    parser = OptionParser(usage='lala.py [OPTIONS]', description='A slick yet powerful mpd web client')
    parser.add_option('-o', '--host', dest='host', metavar='MPD_HOST', default='localhost', help='The mpd host')
    parser.add_option('-p', '--port', dest='port', metavar='MPD_PORT', default='6600', help='The mpd port')
    parser.add_option('-a', '--pass', dest='password', metavar='MPD_PASS', default='', help='The mpd password')

    (options, args) = parser.parse_args()

    run(options.host, options.port, options.password)
