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
#   Copyright (C) 2010 Sofian Brabez <sbz@6dev.net>
#
# Special thanks to the Paramiko project.
#

import sys

from binascii import hexlify
from optparse import OptionParser

from paramiko import DSSKey
from paramiko import RSAKey
from paramiko.ssh_exception import SSHException
from paramiko.py3compat import u

import os.path

class KTunnelKeyGen:
    default_values = {
        "ktype": "rsa",
        "bits": 2048,
        "filename": os.path.expanduser("~") + os.path.sep + "key-ktunnel",
        "comment": "Konekt Tunnel Key",
        "phrase": None
        }
    key_dispatch_table = {
        'dsa': DSSKey,
        'rsa': RSAKey,
        }
    
    def progress(self,arg=None):
        if not arg:
            sys.stdout.write('0%\x08\x08\x08 ')
            sys.stdout.flush()
        elif arg[0] == 'p':
            sys.stdout.write('25%\x08\x08\x08\x08 ')
            sys.stdout.flush()
        elif arg[0] == 'h':
            sys.stdout.write('50%\x08\x08\x08\x08 ')
            sys.stdout.flush()
        elif arg[0] == 'x':
            sys.stdout.write('75%\x08\x08\x08\x08 ')
            sys.stdout.flush()
            
    def genKeys(self,ktype=default_values['ktype'],bits=default_values['bits'],filename=default_values['filename'],phrase=default_values['phrase'],comment=default_values['comment'],verbose=False):
        pfunc = None
        if verbose:
            pfunc = self.progress
            sys.stdout.write("Generating priv/pub %s %d bits key pair (%s/%s.pub)..." % (ktype, bits, filename, filename))
            sys.stdout.flush()
            
        if ktype == 'dsa' and bits > 1024:
            raise SSHException("DSA Keys must be 1024 bits")
        if ktype not in self.key_dispatch_table:
            raise SSHException("Unknown %s algorithm to generate keys pair" % ktype)
        
        # generating private key
        prv = self.key_dispatch_table[ktype].generate(bits=bits, progress_func=pfunc)
        prv.write_private_key_file(filename, password=phrase)
        
        # generating public key
        pub = self.key_dispatch_table[ktype](filename=filename, password=phrase)
        with open("%s.pub" % filename, 'w') as f:
            f.write("%s %s" % (pub.get_name(), pub.get_base64()))
            if comment != None:
                f.write(" %s" % comment)

        if verbose:
            print("done.")
            print("")
            print("")
            print("")
            print("Paste the following key between the 'BEGIN' and 'END' statements")
            print("into the Konekt Dashboard at https://dashboard.konekt.io")
            print("")
            print("-----BEGIN RSA PUBLIC KEY-----")
            print(open("%s.pub" % filename, 'r').read())
            print("-----END RSA PUBLIC KEY-----")
            print("")
            print("")
            hash = u(hexlify(pub.get_fingerprint()))
            print("Fingerprint: %d %s %s.pub (%s)" % (bits, ":".join([ hash[i:2+i] for i in range(0, len(hash), 2)]), filename, ktype.upper()))


