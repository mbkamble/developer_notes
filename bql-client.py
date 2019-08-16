#!/usr/bin/env python3

import socket, sys, os, re, argparse, pexpect

aparser = argparse.ArgumentParser(
    description='bean-query client')
aparser.add_argument('-i', '--id', required=True, help='identifier in %Y format year')
args = aparser.parse_args()
# Create a UDS socket
server_address = os.path.join(
    '/tmp', *["bqlsrvr" + str(os.getuid()), "bql_" + args.id])
sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

# Connect the socket to the port where the server is listening
print('connecting to {}'.format(server_address), file=sys.stderr)
try:
    sock.connect(server_address)
except:
    e = sys.exc_info()[0]
    print('Error: {}'.format(e), file=sys.stderr)
    sys.exit(1)

while True:
    try:
        message = input('>> ') + '\n'
    except EOFError:
        message = ""
    if message:
        try:
            print("sending: {}".format(message))
            sock.sendall(message.encode('utf-8'))
            print("sending complete")
            data = sock.recv(16).decode('utf-8')
            while not re.search("\n", data, re.S):
                data += sock.recv(16).decode('utf-8')
            size, data = data.split('\n', 1)
            while len(data) < int(size):
                data += sock.recv(16).decode('utf-8')
            print('resp>> {}'.format(data), file=sys.stderr)
        except Exception as e:
            print('Exception: {}'.format(str(e)))
    else:
        break

if sock:
    print('codeloc2: closing socket', file=sys.stderr)
    sock.close()
