#!/usr/bin/python
import socket, sys, select
import time, os, shutil, subprocess, commands
import contextlib
import distutils.util
import pyjsonrpc, socket

container = sys.argv[1]
port = sys.argv[2]
status_server = "192.168.20.19:9001"

# helpers
# https://blog.csdn.net/u013314786/article/details/78962103
def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("baidu.com", 80))
    ip = s.getsockname()[0]
    s.close()
    return ip
    
if __name__ == "__main__":
    ip = get_ip()
    retvar = 1
    try:
        # remote test: query status_server
        status_cli = pyjsonrpc.HttpClient(url = "http://%s/jsonrpc" % status_server)
        cip = status_cli.get_container(container)
        if len(cip) == 0:
            print "- no entry in status_server: %s" % container
        elif cip == ip: retvar = 0
        else: retvar = 1
        print "- check %s %s: [query]%d" % (container, port, retvar)
    except:
        # local test: netstat
        # print "- status_server is not available. fall back to service test."
        retvar, out = commands.getstatusoutput("netstat -nl |grep %s" % port)
        if retvar != 0: retvar = 1
        print "- check %s %s: [netstat]%d" % (container, port, retvar)
    sys.exit(retvar)

