#!/usr/bin/python
import socket, sys, select, signal, threading
import time, os, shutil, subprocess, commands, pprint
import contextlib
import distutils.util
import pyjsonrpc

base_path = "/home/islab/src/dockermig/containers/"

class StatusService(pyjsonrpc.HttpRequestHandler):

    def __init__(self):
        self.containers = {}
 
    # service management APIs
    @pyjsonrpc.rpcmethod
    def set_container(self, name, ip):
        print "- set container=%s ip=%s" % (name, ip)
        self.containers[name] = ip
        
    @pyjsonrpc.rpcmethod
    def get_container(self, name):
        ret = self.containers.get(name, "")
        print "- get container=%s -> ip=%s -" % (name, ret)
        return ret
        
svr = pyjsonrpc.ThreadingHttpServer(server_address=("0.0.0.0", 9001), RequestHandlerClass=StatusService)
svr.allow_reuse_address = True   
def server():
    print "- start status server thread %d" % os.getpid()
    svr.serve_forever()
    print "- server thread exiting..."

if __name__ == "__main__":
    th = threading.Thread(target=server)
    th.setDaemon(True)
    th.start()
    try:
        while True: pass
    except KeyboardInterrupt:
        print "- ctrl-c %d " % os.getpid()
        svr.shutdown()
        th.join()

