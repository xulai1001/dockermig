#!/usr/bin/python
import socket, sys, select
import time, os, shutil, subprocess, commands
import contextlib
import distutils.util
import pyjsonrpc

base_path = "/home/islab/src/dockermig/containers/"

# helpers
# https://stackoverflow.com/questions/6194499/pushd-through-os-system
@contextlib.contextmanager
def pushd(d):
    last_dir = os.getcwd()
    os.chdir(d)
    print "> entering %s" % d
    yield
    print "> leaving %s" % d
    os.chdir(last_dir)

retvar = 0
def warn_on_error():
    global retvar
    if retvar != 0:
        print "- error: %d..." % retvar

def run_cmd_timed(cmd):
    global retvar
    print "- " + cmd
    st = time.time()
    retvar = os.system(cmd)
    warn_on_error()
    print "- time: %.2g s" % (time.time() - st)
    
def start_kad():
    print "- start keepalived..."
    os.system("keepalived -d")
    os.system("gnome-terminal -t 'Keepalived log' -- tail -f /var/log/syslog")

class MigrateService(pyjsonrpc.HttpRequestHandler):
    @pyjsonrpc.rpcmethod
    def prepare(self, client_ip, container):
        print "> prepare to migrate: %s from %s" % (container, client_ip)
        bundle_path = base_path + container + "/bundle/"
        os.system("mkdir -p %s" % bundle_path)
        with pushd(bundle_path):
            os.system("rm -rf predump checkpoint")
        return bundle_path
        
    @pyjsonrpc.rpcmethod        
    def restore(self, container):
        print "> restore: %s" % container
        bundle_path = base_path + container + "/bundle/"
        start_kad()
        with pushd(bundle_path):
            print "- restore symlink..."
            print "ln -s %s/predump checkpoint/parent" % bundle_path
            os.system("ln -s %s/predump checkpoint/parent" % bundle_path)
            run_cmd_timed("gnome-terminal -- /home/islab/src/dockermig/scripts/run.sh runc restore --tcp-established --shell-job --image-path checkpoint --work-path checkpoint %s" % container)
        return retvar
        
    @pyjsonrpc.rpcmethod
    def lazy_restore(self, client_ip, container):
        print "> lazy-restore: %s from %s" % (container, client_ip)
        start_kad()
        bundle_path = base_path + container + "/bundle/"
        with pushd(bundle_path):
            print "- restore symlink..."
            print "ln -s %s/predump checkpoint/parent" % bundle_path
            os.system("ln -s %s/predump checkpoint/parent" % bundle_path)
            print "- connect lazy-page server"
            os.system("gnome-terminal -t 'CRIU lazy-pages' -- /home/islab/src/dockermig/scripts/run.sh criu lazy-pages --tcp-established --page-server --address %s --port 27000 -vv -D checkpoint -W checkpoint" % client_ip)
#            time.sleep(1)
            print "- live restore container"
            run_cmd_timed("gnome-terminal -t 'Container - %s' -- /home/islab/src/dockermig/scripts/run.sh runc restore --tcp-established --shell-job --image-path checkpoint --work-path checkpoint --lazy-pages %s" % (container, container))
        return retvar

if __name__ == "__main__":
    svr = pyjsonrpc.ThreadingHttpServer(
        server_address = ('0.0.0.0', 9000), RequestHandlerClass = MigrateService)
    print "- start migrate server..."
    svr.serve_forever()
