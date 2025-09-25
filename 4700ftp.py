#!/usr/bin/env python3
# 4700ftp.py
# johnmark bermudez
# cs4700 - project 2

import socket
import sys
import os
from urllib.parse import urlparse

# handles sending/receiving messages to the server
def send_cmd(sock, cmd, verbose=False):
    if verbose:
        print(f"--> {cmd.strip()}", file=sys.stderr)
    sock.sendall(cmd.encode())
    
def get_resp(sock, verbose=False):
    resp = sock.recv(4096).decode()
    if verbose:
        print(f"<-- {resp.strip()}", file=sys.stderr)
    return resp

# opens the second socket for data transfer (like for ls or cp)
def open_data_sock(ctrl_sock, verbose=False):
    send_cmd(ctrl_sock, "PASV\r\n", verbose)
    resp = get_resp(ctrl_sock, verbose)
    if not resp.startswith('227'):
        print(f"error: could not enter passive mode: {resp.strip()}", file=sys.stderr)
        return None
    
    # parse the ip and port from the server's response
    try:
        parts = resp.split('(')[1].split(')')[0].split(',')
        ip = '.'.join(parts[:4])
        port = (int(parts[4]) * 256) + int(parts[5])
    except:
        print("error: couldn't parse PASV response", file=sys.stderr)
        return None

    # connect the data socket
    data_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    data_sock.connect((ip, port))
    return data_sock

# main function
def main():
    if len(sys.argv) < 2:
        print("usage: ./4700ftp.py [operation] [params...]", file=sys.stderr)
        sys.exit(1)

    # basic command line parsing
    verbose = '-v' in sys.argv or '--verbose' in sys.argv
    args = [arg for arg in sys.argv[1:] if not arg.startswith('-')]
    
    operation = args[0]
    params = args[1:]

    # figure out which url to use
    url_str = ""
    for p in params:
        if p.startswith('ftp://'):
            url_str = p
            break
    if not url_str:
        print("error: missing remote URL parameter.", file=sys.stderr)
        sys.exit(1)

    # parse the url
    url = urlparse(url_str)
    host = url.hostname
    port = url.port or 21
    user = url.username or 'anonymous'
    passwd = url.password or ''
    path = url.path
    
    # connect to server
    ctrl_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        ctrl_sock.connect((host, port))
    except socket.error as e:
        print(f"error connecting to {host}:{port}: {e}", file=sys.stderr)
        sys.exit(1)

    # get welcome message
    resp = get_resp(ctrl_sock, verbose)
    if not resp.startswith('220'):
        print(f"error: server not ready: {resp.strip()}", file=sys.stderr)
        ctrl_sock.close()
        sys.exit(1)

    # login
    send_cmd(ctrl_sock, f"USER {user}\r\n", verbose)
    resp = get_resp(ctrl_sock, verbose)
    if resp.startswith('331'):
        send_cmd(ctrl_sock, f"PASS {passwd}\r\n", verbose)
        resp = get_resp(ctrl_sock, verbose)
        if not resp.startswith('230'):
            print(f"error: login failed: {resp.strip()}", file=sys.stderr)
            ctrl_sock.close()
            sys.exit(1)

    # set binary mode for transfers
    send_cmd(ctrl_sock, "TYPE I\r\n", verbose)
    get_resp(ctrl_sock, verbose)


    # operation logic
    try:
        if operation == 'ls':
            data_sock = open_data_sock(ctrl_sock, verbose)
            if data_sock:
                send_cmd(ctrl_sock, f"LIST {path}\r\n", verbose)
                get_resp(ctrl_sock, verbose) # 150 response
                
                while True:
                    data = data_sock.recv(4096)
                    if not data:
                        break
                    print(data.decode(), end='')
                
                data_sock.close()
                get_resp(ctrl_sock, verbose) # 226 response

        elif operation == 'mkdir':
            send_cmd(ctrl_sock, f"MKD {path}\r\n", verbose)
            get_resp(ctrl_sock, verbose)

        elif operation == 'rmdir':
            send_cmd(ctrl_sock, f"RMD {path}\r\n", verbose)
            get_resp(ctrl_sock, verbose)

        elif operation == 'rm':
            send_cmd(ctrl_sock, f"DELE {path}\r\n", verbose)
            get_resp(ctrl_sock, verbose)

        elif operation == 'cp' or operation == 'mv':
            if len(params) != 2:
                print("error: cp/mv requires a source and destination", file=sys.stderr)
                sys.exit(1)
            
            src, dst = params[0], params[1]
            # upload
            if not src.startswith('ftp://'): 
                lpath, rpath = src, url.path
                data_sock = open_data_sock(ctrl_sock, verbose)
                if data_sock:
                    send_cmd(ctrl_sock, f"STOR {rpath}\r\n", verbose)
                    get_resp(ctrl_sock, verbose) # 150
                    with open(lpath, 'rb') as f:
                        while True:
                            chunk = f.read(4096)
                            if not chunk:
                                break
                            data_sock.sendall(chunk)
                    data_sock.close()
                    get_resp(ctrl_sock, verbose) # 226
                if operation == 'mv':
                    os.remove(lpath)
            # download
            else: 
                rpath, lpath = url.path, dst
                data_sock = open_data_sock(ctrl_sock, verbose)
                if data_sock:
                    send_cmd(ctrl_sock, f"RETR {rpath}\r\n", verbose)
                    get_resp(ctrl_sock, verbose) # 150
                    with open(lpath, 'wb') as f:
                        while True:
                            chunk = data_sock.recv(4096)
                            if not chunk:
                                break
                            f.write(chunk)
                    data_sock.close()
                    get_resp(ctrl_sock, verbose) # 226
                if operation == 'mv':
                    send_cmd(ctrl_sock, f"DELE {rpath}\r\n", verbose)
                    get_resp(ctrl_sock, verbose)
        else:
            print(f"error: unknown operation '{operation}'", file=sys.stderr)

    except Exception as e:
        print(f"an unexpected error occurred: {e}", file=sys.stderr)

    # clean up
    send_cmd(ctrl_sock, "QUIT\r\n", verbose)
    get_resp(ctrl_sock, verbose)
    ctrl_sock.close()


main()