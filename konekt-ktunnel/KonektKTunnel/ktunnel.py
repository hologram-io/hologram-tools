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

"""
Tool to perform local port forwarding through the Konekt Inbound Tunnel

This script connects to the Konekt Inbound Tunnel server and sets up
local port forwarding (analogous to OpenSSH's "-L" option) from a 
local port through the Konekt server.
"""

import getpass
import os
import socket
import select
try:
    import SocketServer
except ImportError:
    import socketserver as SocketServer
import sys
from optparse import OptionParser
import paramiko

SSH_PORT = 22
DEFAULT_PORT = 9999
DEFAULT_LOCAL_HOST = '127.0.0.1'

DEFAULT_SERVER_HOST = 'tunnel.konekt.io'
DEFAULT_SERVER_PORT = 998

g_verbose = True


class ForwardServer (SocketServer.ThreadingTCPServer):
    daemon_threads = True
    allow_reuse_address = True
    

class Handler (SocketServer.BaseRequestHandler):

    def handle(self):
        try:
            chan = self.ssh_transport.open_channel('direct-tcpip',
                                                   (self.chain_host, self.chain_port),
                                                   self.request.getpeername())
        except Exception as e:
            verbose('Incoming request to %s:%d failed: %s' % (self.chain_host,
                                                              self.chain_port,
                                                              repr(e)))
            return
        if chan is None:
            verbose('Incoming request to %s:%d was rejected by the server.' %
                    (self.chain_host, self.chain_port))
            return

        verbose('Connected!  Tunnel open %r -> %r -> %r' % (self.request.getpeername(),
                                                            chan.getpeername(), (self.chain_host, self.chain_port)))
        while True:
            r, w, x = select.select([self.request, chan], [], [])
            if self.request in r:
                data = self.request.recv(1024)
                if len(data) == 0:
                    break
                chan.send(data)
            if chan in r:
                data = chan.recv(1024)
                if len(data) == 0:
                    break
                self.request.send(data)
                
        peername = self.request.getpeername()
        chan.close()
        self.request.close()
        verbose('Tunnel closed from %r' % (peername,))


def forward_tunnel(local_host, local_port, remote_host, remote_port, transport):
    # this is a little convoluted, but lets me configure things for the Handler
    # object.  (SocketServer doesn't give Handlers any way to access the outer
    # server normally.)
    class SubHander (Handler):
        chain_host = remote_host
        chain_port = remote_port
        ssh_transport = transport
    ForwardServer((local_host, local_port), SubHander).serve_forever()


def verbose(s):
    if g_verbose:
        print(s)


HELP = """\
Tool to perform local port forwarding through the Konekt Inbound Tunnel. This script connects to the Konekt Inbound Tunnel server and sets up local port forwarding (analogous to OpenSSH's "-L" option) from a local port through the Konekt server. A local port (given with -p) is forwarded across the tunnel to a device:port from behind the Konekt firewall. To use, it is necessary to first visit https://dashboard.konekt.io and configure the inbound tunnel for your devices.
"""


def get_host_port(spec, default_port):
    "parse 'hostname:22' into a host and port, with the port optional"
    args = (spec.split(':', 1) + [default_port])[:2]
    args[1] = int(args[1])
    return args[0], args[1]


def parse_options():
    global g_verbose
    
    parser = OptionParser(usage='usage: %prog [options] <server-host>[:<server-port>]',
                          version='%prog 1.0', description=HELP)
    parser.add_option('-d', '--device', action='store', type='string', dest='remote', default=None, metavar='DEVICEIDENTIFIER:port',
                      help='device and port to forward to (DEVICEIDENTIFIER can be "<device ID>.id.device" or "<SIM NUMBER>.sim.device", minus the quotes)')
    parser.add_option('-b', '--local-host', action='store', type='string', dest='host',
                      default=DEFAULT_LOCAL_HOST,
                      help='local host IP to bind to (default: %s)' % DEFAULT_LOCAL_HOST)
    parser.add_option('-p', '--local-port', action='store', type='int', dest='port',
                      default=DEFAULT_PORT,
                      help='local port to forward (default: %d)' % DEFAULT_PORT)
    parser.add_option('-u', '--user', action='store', type='string', dest='user',
                      default=None,
                      help='username for authentication')
    parser.add_option('-q', '--quiet', action='store_false', dest='verbose', default=True,
                      help='squelch all informational output')
    parser.add_option('-K', '--key', action='store', type='string', dest='keyfile',default=os.path.expanduser('~') + os.path.sep + 'key-ktunnel',
                      help='ADVANCED: private key file to use for authentication, normally not required')
    #parser.add_option('', '--no-key', action='store_false', dest='look_for_keys', default=True,
    #                  help='don\'t look for or use a private key file')
    parser.add_option('-P', '--password', action='store_true', dest='readpass', default=False,
                      help='ADVANCED: read password (for unlocking key) from stdin, normally not required')
    options, args = parser.parse_args()

    #if len(args) < 1:
    #    parser.error('Incorrect number of arguments.')

    if options.user is None:
        options.user = raw_input('Enter numerical user ID: ')
        if len(options.user) < 1:
            options.user = None

    if options.remote is None:
        device_identifier = raw_input('Enter SIM number of remote device: ')
        if len(device_identifier) < 1:
            device_identifier = raw_input('Enter numerical device ID of remote device: ')
            if len(device_identifier) > 0:
                options.remote = device_identifier + '.id.device'
        else:
            options.remote = device_identifier + '.sim.device'
        port = raw_input('Enter remote device port: ')
        if len(port) > 0:
            options.remote = options.remote + ':' + port

    if (not (options.remote is None)):
        verbose('DEVICEIDENTIFIER is set to: ' + options.remote)

    if options.user is None:
        parser.error('User ID is required (-u).')
    if options.remote is None:
        parser.error('Remote device and port required (-d).')
    

    g_verbose = options.verbose
    server_host = DEFAULT_SERVER_HOST
    server_port = DEFAULT_SERVER_PORT
    if(len(args) > 0):
        server_host, server_port = get_host_port(args[0], DEFAULT_SERVER_PORT)

    remote_host, remote_port = get_host_port(options.remote, SSH_PORT)
    return options, (server_host, server_port), (remote_host, remote_port)


def main():
    options, server, remote = parse_options()

    password = None
    if options.readpass:
        password = getpass.getpass('Enter password: ')

    client = paramiko.SSHClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(paramiko.WarningPolicy())

    verbose('Loading access credentials...')
    try:
        # Check to see if keyfile exists
        open(options.keyfile,'r')
    except:
        # If not, automatically generate some new keys!
        import KTunnelLib
        gen = KTunnelLib.KTunnelKeyGen()
        gen.genKeys(filename=options.keyfile,comment=gen.default_values['comment'] + ' AUTO',verbose=True)
        gen = None
        print('')
        print('Key generated. Before re-running command, copy and paste above key into https://dashboard.konekt.io')
        print('Exiting.')
        sys.exit(1)

        
    verbose('Connecting to server %s:%d ...' % (server[0], server[1]))
    try:
        client.connect(server[0], server[1], username=options.user, key_filename=options.keyfile,
                       look_for_keys=True, password=password)
    except Exception as e:
        if (e[0] == 'not a valid EC private key file'):
            print('')
            print('*** AUTHENTICATION ERROR: Please ensure the key, below, has been added as')
            print('an authorized key.')
            print('')
            print('')
            print("Paste the following key between the 'BEGIN' and 'END' statements")
            print('into the Konekt Dashboard at https://dashboard.konekt.io')
            print('')
            print('-----BEGIN RSA PUBLIC KEY-----')
            print(open("%s.pub" % options.keyfile, 'r').read())
            print('-----END RSA PUBLIC KEY-----')
            print('')
        else:
            print('*** Failed to connect to %s:%d: %r' % (server[0], server[1], e))
        sys.exit(1)

    verbose('Now forwarding %s:%d to %s:%d ...' % (options.host, options.port, remote[0], remote[1]))

    try:
        forward_tunnel(options.host, options.port, remote[0], remote[1], client.get_transport())
    except KeyboardInterrupt:
        verbose('C-c: Port forwarding stopped.')
        verbose('Exiting.')
        sys.exit(0)


if __name__ == '__main__':
    main()
