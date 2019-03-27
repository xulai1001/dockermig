#!/usr/bin/python
import socket, sys, select, signal, threading
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
    
def wait_ip(ipaddr):
    down = True
    while down:
        try:
            test_socket = socket.socket()
            test_socket.bind((ipaddr, 27001))
        except: continue
        down = False
        print "- ip %s is up" % ipaddr
        
def new_window(title, cmdline):
    print "> w: %s, cmd: %s" % (title, cmdline)
    os.system("gnome-terminal -t '%s' -- /home/islab/src/dockermig/scripts/run.sh %s" % (title, cmdline))
    
def getsize(path):
    global retvar
    retvar, sz = commands.getstatusoutput("du -hs %s" % path)
    return sz
    
def print_fw():
    print "- fw rules:"
    os.system("sudo iptables -nL --line-numbers")
#    print "---------------------------"
#    os.system("sudo iptables -t nat -L")
#    print "---------------------------"
#    os.system("sudo iptables -t mangle -L")
        
extensions = "--tcp-established --shell-job --file-locks"

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
            new_window("Restore - %s" % container,
                       "runc --debug restore %s --image-path checkpoint --work-path checkpoint --bundle %s %s" % (extensions, bundle_path, container))
            time.sleep(2)
            print "- tweak fw rules"
            os.system("iptables -F")
            os.system("iptables -t nat -F")
        return retvar
        
    @pyjsonrpc.rpcmethod
    def lazy_restore(self, client_ip, container):
        print "> lazy-restore: %s from %s" % (container, client_ip)
        start_kad() # start keepalived
        print "- wait for ip address takes effect..."
        wait_ip("192.168.100.100")
        bundle_path = base_path + container + "/bundle/"
        with pushd(bundle_path):
            print "- restore symlink..."
            print "ln -s %s/predump checkpoint/parent" % bundle_path
            os.system("unlink checkpoint/parent")
            os.system("ln -s %s/predump checkpoint/parent" % bundle_path)
            
            print "- connect lazy-page server"
            new_window("CRIU lazy-pages",
                       "criu lazy-pages --tcp-established -j -l --page-server --address %s --port 27000 -vvvv -D checkpoint -W checkpoint" % client_ip)
            print "- live restore container"
            new_window("Restore - %s" % container, 
                       "runc --debug restore %s --image-path checkpoint --work-path checkpoint --bundle %s --lazy-pages %s" % (extensions, bundle_path, container))
            time.sleep(2)
            print "- tweak fw rules"
            os.system("iptables -D CRIU -j DROP")
            print_fw()

        return retvar
        
svr = pyjsonrpc.ThreadingHttpServer(server_address=("0.0.0.0", 9000), RequestHandlerClass=MigrateService)    
def server():
    print "- start migrate server thread %d" % os.getpid()
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

