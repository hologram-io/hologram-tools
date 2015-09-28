#!/usr/bin/env python
# Copyright 2015 Konekt, Inc.
#
# Author: Pat Wilbur <hello@konekt.io> <pdub@pdub.net>
#
# This file is part of ktunnel
#
# KTunnel is free software; you can redistribute it and/or modify it under the
# terms of the GNU Lesser General Public License as published by the Free
# Software Foundation; either version 2.1 of the License, or (at your option)
# any later version.
#
# KTunnel is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with KTunnel; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Suite 500, Boston, MA  02110-1335  USA.
#
# This file is based upon a file, licensed under the LGPL, distributed with
# the Paramiko project and with the original copyright notice:
# 
#   Copyright (C) 2003-2007  Robey Pointer <robeypointer@gmail.com> 
#
# Special thanks to the Paramiko project.
#

longdesc = '''
This is a tool for connecting to the Konekt Inbound Tunnel server
and accessing devices within the Konekt network.

Required packages:
    paramiko
'''

import sys
try:
    from setuptools import setup
    kw = {
        'install_requires': [
            'paramiko >= 1.15'
        ],
    }
except ImportError:
    from distutils.core import setup
    kw = {}

if sys.platform == 'darwin':
    import setup_helper
    setup_helper.install_custom_make_tarball()

version = '1.0.0'

setup(
    name = "ktunnel",
    version = version,
    description = "Konekt Inbound Tunnel client for https://konekt.io",
    long_description = longdesc,
    author = "Pat Wilbur",
    author_email = "hello@konekt.io",
    url = "https://github.com/konektlabs/tools/konekt-ktunnel/",
    packages = [ 'KonektKTunnel' ],
    scripts = ["ktunnel", "ktunnel-keygen"],
    license = 'LGPL',
    platforms = 'Posix; MacOS X; Windows',
    classifiers = [
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)',
        'Operating System :: OS Independent',
        'Topic :: Internet',
        'Topic :: Security :: Cryptography',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
    ],
    **kw
)
