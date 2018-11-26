#!/usr/bin/python
import socket, sys, select
import time, os, shutil, subprocess, commands
import contextlib
import distutils.util
import pyjsonrpc, socket

server = sys.argv[1]
container = sys.argv[2]
username = "ubuntu"
cli = None
base_path = ""

# helpers
# https://stackoverflow.com/questions/6194499/pushd-through-os-system
@contextlib.contextmanager
def pushd(d):
    last_dir = os.getcwd()
    os.chdir(d)
    print "> entering %s" % d
    yield
    os.chdir(last_dir)

retvar = 0
def exit_on_error():
    global retvar
    if retvar != 0:
        print "- error: %d, exiting..." % retvar
        sys.exit(retvar)  

def run_cmd_timed(cmd):
    global retvar
    print "- " + cmd
    st = time.time()
    retvar = os.system(cmd)
    exit_on_error()
    print "- time: %.2g s" % (time.time() - st)
    
# restore routines     
def restore(self, container):
    print "> restore: %s" % container
    run_cmd_timed("gnome-terminal -- /usr/local/sbin/runc restore --image-path checkpoint --work-path checkpoint %s" % container)
    
def lazy_restore(self, svr, port, c):
    print "> lazy-restore: %s from %s:%d" % (c, svr, port)
    run_cmd_timed("gnome-terminal -- /usr/local/sbin/runc restore --image-path checkpoint --work-path checkpoint --lazy-pages %s" % c
    run_cmd_timed("criu lazy-pages --page-server --address %s --port %d -vv -D checkpoint -W checkpoint" % (svr, port))
    return retvar

# api calls
def check_running(c):
    print "- check if container is running..."
    ret = cli.list()
    print ret

def pull_rootfs():
    print "- pull ROOTFS from %s" % dest
    os.system("mkdir -p rootfs")
    run_cmd_timed("rsync -aqz %s:%s rootfs/" % (server, base_path+"rootfs"))
    os.system("scp %s:%s/config.json ." % (server, base_path))
    
def pull_predump():
    print "- pull PRE-DUMP..."
    os.system("mkdir -p predump")
    run_cmd_timed("rsync -aqz %s:%s predump/" % (server, base_path+"predump"))
    
def pull_checkpoint():
    print "- pull CHECKPOINT..."
    os.system("mkdir -p checkpoint")
    run_cmd_timed("rsync -aqz %s:%s checkpoint/" % (server, base_path+"checkpoint"))
    
if __name__ == "__main__":
    global cli
    global base_path
    print "- migrate %s from %s" % (container, server)
    print "- connect to %s" % server
    cli = pyjsonrpc.HttpClient(url = "http://%s:9000/jsonrpc" % dest)
    base_path = cli.base_path(container)
    
    os.system("mkdir -p bundle")
    with pushd("bundle"):
        check_running(container)
        pull_rootfs()
        cli.predump(container)
        pull_predump()
        ret = cli.lazy_dump(container)
        pull_checkpoint()
        lazy_restore(server, ret["port"], container)
        
