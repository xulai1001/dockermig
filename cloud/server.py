#!/usr/bin/python
import socket, sys, select
import time, os, shutil, subprocess, commands
import contextlib
import distutils.util
import pyjsonrpc

base_path = "/home/ubuntu/src/dockermig/containers/"

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
    
def bundle(c):
    return base_path + c + "/bundle/"
        
# act as sender. client pulls container from us.
# we must have unique IP. client need not
class CloudMigrateService(pyjsonrpc.HttpRequestHandler):

    @pyjsonrpc.rpcmethod
    def base_path(self, container):
        return bundle(container)
        
    # remotely starts a container
    @pyjsonrpc.rpcmethod
    def run(self, container):
        print "> start container: %s" % container
        with pushd(bundle(container)):
            run_cmd_timed('tmux split-window -h "sudo runc run %s"' % container)
        return container
        
    @pyjsonrpc.rpcmethod
    def list(self):
        print "> list containers"
        retvar, ret = commands.getstatusoutput("sudo runc list")
        return ret
        
    @pyjsonrpc.rpcmethod
    def predump(self, container):
        print "> start predump: %s" % container
        with pushd(bundle(container)):
            os.system("rm -rf predump checkpoint")
            run_cmd_timed("sudo runc checkpoint --pre-dump --image-path predump %s" % container)
            retvar, psize = commands.getstatusoutput("du -hs predump")
        return dict(path=bundle(container)+ "predump", size=psize)
        
    @pyjsonrpc.rpcmethod
    def checkpoint_dump(self, container):
        print "> start checkpoint dump: %s" % container
        with pushd(bundle(container)):
            run_cmd_timed("sudo runc checkpoint --image-path checkpoint --parent-path predump %s" % container)
            retvar, csize = commands.getstatusoutput("du -hs checkpoint")
        return dict(path=bundle(container)+ "checkpoint", size=csize)
        
    @pyjsonrpc.rpcmethod
    def lazy_dump(self, container):
        global retvar
        with pushd(bundle(container)):
            cmd = """sudo runc checkpoint --image-path checkpoint --lazy-pages --page-server 0.0.0.0:27000 --status-fd copy_pipe %s""" % container    
            if os.path.exists("copy_pipe"):
                os.unlink("copy_pipe")
            os.mkfifo("copy_pipe")
       
            print "- " + cmd
            st = time.time()
            p = subprocess.Popen(cmd, shell=True)
            cp = os.open("copy_pipe", os.O_RDONLY)
            x = os.read(cp, 1)
            if x == "\0":
                print "- ready for lazy page copy..."
            print "- time: %.2g s, retvar: %d" % (time.time() - st, retvar)
            retvar, csize = commands.getstatusoutput("du -hs checkpoint")
        return dict(path=bundle(container)+"checkpoint", size=csize, port=27000)
        
# act as receiver. receives container from client host
# both the client and us must have unique IP.
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
        with pushd(bundle_path):
            run_cmd_timed("gnome-terminal -- /usr/local/sbin/runc restore --image-path checkpoint --work-path checkpoint %s" % container)
        return retvar
        
    @pyjsonrpc.rpcmethod
    def lazy_restore(self, client_ip, container):
        print "> lazy-restore: %s from %s" % (container, client_ip)
        bundle_path = base_path + container + "/bundle/"
        with pushd(bundle_path):
            run_cmd_timed("gnome-terminal -- /usr/local/sbin/runc restore --image-path checkpoint --work-path checkpoint --lazy-pages %s" % container)
            run_cmd_timed("criu lazy-pages --page-server --address %s --port 27000 -vv -D checkpoint -W checkpoint" % client_ip)
        return retvar

if __name__ == "__main__":
    svr = pyjsonrpc.ThreadingHttpServer(
#        server_address = ('0.0.0.0', 9000), RequestHandlerClass = MigrateService)
        server_address = ('0.0.0.0', 9000), RequestHandlerClass = CloudMigrateService)

    print "- start migrate server..."
    print "- note: the cloud version should run under TMUX"
    svr.serve_forever()
