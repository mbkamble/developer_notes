#!/usr/bin/env python3

import socket, sys, os, re, argparse, pexpect

aparser = argparse.ArgumentParser(
    description='bean-query server dedicated for a given source file')
aparser.add_argument('-b', '--bctfile', required=True)
args = aparser.parse_args()

basename = os.path.basename(args.bctfile)
uniqid = re.search("(\d{4})", basename).group(1)
server_address = os.path.join(
    '/tmp', *["bqlsrvr" + str(os.getuid()), "bql_" + uniqid])

# Make sure the socket does not already exist
try:
    os.makedirs(os.path.dirname(server_address), exist_ok=True)
    os.unlink(server_address)
except OSError:
    if os.path.exists(server_address):
        raise

# Create a UDS socket
sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
# Bind the socket to the port
print('starting up on {}'.format(server_address), file=sys.stderr)
sock.bind(server_address)

# spawn the bean-query app
os.environ['PAGER'] = 'cat'
bql = pexpect.spawn("bean-query {}".format(args.bctfile))
bql.expect("beancount> ")
print("file {} loaded in bean-query".format(args.bctfile))

# Listen for incoming connections
sock.listen(1)

while True:
    # Wait for a connection
    print('waiting for a connection', file=sys.stderr)
    connection, client_address = sock.accept()
    try:
        print('connection from {}'.format(client_address), file=sys.stderr)

        # Receive the data in small chunks and retransmit it
        req = ""
        while True:
            data = connection.recv(16).decode('utf-8')
            if data:
                print("codeloc1: data={}".format(data))
                req += data
                if re.search('\n', req, re.S):
                    cmd, req = req.split('\n', 1)
                    print("cmd>> {}".format(cmd), file=sys.stderr)
                    bql.sendline(cmd)
                    bql.expect("beancount> ")
                    resp = bql.before
                    # resp = "\n".join(
                    #     ["iter {}: {}".format(x, cmd) for x in range(0,3)])
                    connection.sendall("{}\n{}".format(len(resp), resp).encode('utf-8'))
            else:
                print('no more data from {}'.format(client_address), file=sys.stderr)
                connection.close()
                break

    finally:
        # Clean up the connection
        print('codeloc2: closing connection', file=sys.stderr)
        connection.close()
