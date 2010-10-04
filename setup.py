#!/usr/bin/env python
# -*- coding: utf-8 -*-

from distutils.core import setup

setup(
    name='lala', 
    version='0.1',
    description='A slick yet powerful mpd web client',
    author='Oliver Mader',
    author_email='b52@reaktor42.de',
    url='http://reaktor42.de/projects/lala',
    requires=['flask'],
    packages=['lala'],
    package_data={'lala': ['static/*/*', 'templates/*']},
)
