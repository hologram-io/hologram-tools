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
# 
#
# This file is part of paramiko.
#
# Paramiko is free software; you can redistribute it and/or modify it under the
# terms of the GNU Lesser General Public License as published by the Free
# Software Foundation; either version 2.1 of the License, or (at your option)
# any later version.
#
# Paramiko is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Paramiko; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA.

import sys

from binascii import hexlify
from optparse import OptionParser

from paramiko import DSSKey
from paramiko import RSAKey
from paramiko.ssh_exception import SSHException
from paramiko.py3compat import u
import KTunnelLib

def main():
    usage="""
%prog [-v] [-b bits] -t type [-N new_passphrase] [-f output_keyfile]"""
    
    gen = KTunnelLib.KTunnelKeyGen()

    parser = OptionParser(usage=usage)
    parser.add_option("-t", "--type", type="string", dest="ktype",
        help="Specify type of key to create (dsa or rsa)",
        metavar="ktype", default=gen.default_values["ktype"])
    parser.add_option("-b", "--bits", type="int", dest="bits",
        help="Number of bits in the key to create", metavar="bits",
        default=gen.default_values["bits"])
    parser.add_option("-N", "--new-passphrase", dest="newphrase",
        help="Provide new passphrase", metavar="phrase")
    parser.add_option("-P", "--old-passphrase", dest="oldphrase",
        help="Provide old passphrase", metavar="phrase")
    parser.add_option("-f", "--filename", type="string", dest="filename",
        help="Filename of the key file", metavar="filename",
        default=gen.default_values["filename"])
    parser.add_option("-q", "--quiet", default=False, action="store_false",
        help="Quiet")
    parser.add_option("-v", "--verbose", default=True, action="store_true",
        help="Verbose")
    parser.add_option("-C", "--comment", type="string", dest="comment",
        help="Provide a new comment", metavar="comment",
        default=gen.default_values["comment"])

    (options, args) = parser.parse_args()

    #if len(sys.argv) == 1:
    #    parser.print_help()
    #    sys.exit(0)

    #for o in list(gen.default_values.keys()):
    #    globals()[o] = getattr(options, o, gen.default_values[o.lower()])

    ktype=getattr(options,'ktype',gen.default_values['ktype'])
    bits=getattr(options,'bits',gen.default_values['bits'])
    filename=getattr(options,'filename',gen.default_values['filename'])
    phrase=getattr(options,'newphrase',gen.default_values['phrase'])
    comment=getattr(options,'comment',gen.default_values['comment'])
    
    if options.newphrase:
        phrase = getattr(options, 'newphrase')

    actually_generate_key = False
    # if using default file, make sure it doesn't already exist so not accidentally overwritten
    try:
        open(filename,'r')
        print("")
        print("*** ERROR: Key file already exists. Overwrite disallowed.")
        print("To override, first delete file.")
        print("")
        print("Deleting the file will prevent further access to the Konekt")
        print("Inbound Tunnel. Deleting will require sending the")
        print("newly-generated new public key to the Konekt Inbound Tunnel")
        print("service before remote connections to devices will be able to")
        print("performed again.")
        print("")
        print("Proceed only if you are absolutely sure that you wish to")
        print("do this.")
        print("")
        print("Key file name: " + filename)
        print("")
        print("Exiting.")
    except:
        actually_generate_key = True
        pass

    if actually_generate_key:
        gen.genKeys(ktype,bits,filename,phrase,comment,options.verbose)

if __name__ == '__main__':
    main()
