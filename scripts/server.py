#!/usr/bin/python
import socket, sys, select, signal, threading
import time, os, shutil, subprocess, commands, pprint
import contextlib
import distutils.util
import pyjsonrpc, json

base_path = "/home/islab/src/dockermig/containers/"
times = {}
sizes = {}
extensions = "--tcp-established --shell-job --file-locks"

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

def run_cmd_timed(cmd, tag=""):
    global retvar
    print "- " + cmd
    st = time.time()
    retvar = os.system(cmd)
    warn_on_error()
    t = time.time() - st
    if len(tag)>0: times[tag] = t
    print "- time: %.2g s" % t
    
def start_kad():
    print "- start keepalived..."
    os.system("keepalived -d")
    #os.system("gnome-terminal -t 'Keepalived log' -- tail -f /var/log/syslog")
    
ip_ready = {}
def wait_ip(ipaddr):
    ip_ready[ipaddr] = False
    down = True
    st = time.time()
    while down:
        try:
            test_socket = socket.socket()
            test_socket.bind((ipaddr, 27001))
        except: continue
        down = False
        ip_ready[ipaddr] = True
    
    t = time.time() - st; times["ipaddr"] = t    
    print "- ip %s is up, Time: %.2g s" % (ipaddr, t)
        
def new_window(title, cmdline):
    print "> w: %s, cmd: %s" % (title, cmdline)
    os.system("gnome-terminal -t '%s' -- /home/islab/src/dockermig/scripts/run.sh %s" % (title, cmdline))
    
def getsize(path):
    global retvar
    retvar, sz = commands.getstatusoutput("du -hs %s" % path)
    sizes[path] = sz
    return sz
    
def print_fw():
    print "- fw rules:"
    os.system("sudo iptables -nL --line-numbers")

def parse_fw():
    lines = os.popen("sudo iptables -nL").readlines()
    result = {}; i=0; j=0
    while i<len(lines):
        if lines[i].startswith("Chain"):
            name = lines[i].split(" ")[1]
            result[name] = []
            i+=2
            while i<len(lines) and not lines[i].startswith("Chain"):
                rule = filter(lambda s: len(s)>0, lines[i].split("  "))
                rule = map(lambda s: s.strip(), rule)
                if len(rule)>1: result[name].append(rule)
                i+=1
        else: i+=1
    # pprint.pprint(result)
    return result
    
def wait_remove_drop_rules():
    found = False
    st = time.time()
    while not found:
        rules = parse_fw()
        if rules.has_key("CRIU"):
            for r in rules["CRIU"]:
                if r[0] == "DROP":
                    found = True
                    break
        time.sleep(0.1)
    # remove the drop rules
    os.system("sudo iptables -D CRIU -j DROP")
    t = time.time() - st; times["tweak_fw"] = t
    print "- found criu drop rule and remove it. Time: %.2g s" % t 

class MigrateService(pyjsonrpc.HttpRequestHandler):

    @pyjsonrpc.rpcmethod
    def prepare(self, client_ip, container):
        print "> prepare to migrate: %s from %s" % (container, client_ip)
        st = time.time()
        bundle_path = base_path + container + "/bundle/"
        os.system("mkdir -p %s" % bundle_path)
        with pushd(bundle_path):
            os.system("rm -rf predump checkpoint")
        t = time.time() - st; times["prepare"] = t
        print "- Time: %.2g s" % t
        return bundle_path
###        
#    @pyjsonrpc.rpcmethod        
#    def restore(self, container):
#        print "> restore: %s" % container
#        bundle_path = base_path + container + "/bundle/"
 #       start_kad()
 #       with pushd(bundle_path):
 #           print "- restore symlink..."
 #           print "ln -s %s/predump checkpoint/parent" % bundle_path
 #           os.system("ln -s %s/predump checkpoint/parent" % bundle_path)
 #           new_window("Restore - %s" % container,
 #                      "runc --debug restore %s --image-path checkpoint --work-path checkpoint --bundle %s %s" % (extensions, bundle_path, container))
 #           time.sleep(2)
 #           print "- tweak fw rules"
 #           os.system("iptables -F")
 #           os.system("iptables -t nat -F")
 #       return retvar
###        
    @pyjsonrpc.rpcmethod
    def move_ip(self, vip):
        print "+ start move_ip..."
        th = threading.Thread(target=wait_ip, args=(vip,), name="wait_ip_thread")
        th.start()
        
    @pyjsonrpc.rpcmethod
    def lazy_restore(self, client_ip, container, vip):
        print "> lazy-restore: %s from %s" % (container, client_ip)
        st = time.time(); times["restore_start"] = st
        # start_kad() # start keepalived
        
        bundle_path = base_path + container + "/bundle/"
        with pushd(bundle_path):
            print "- restore symlink..."
            print "ln -s %s/predump checkpoint/parent" % bundle_path
            os.system("unlink checkpoint/parent")
            os.system("ln -s %s/predump checkpoint/parent" % bundle_path)
            
            print "- connect lazy-page server"
            new_window("CRIU lazy-pages",
                       "criu lazy-pages --tcp-established -j -l --page-server --address %s --port 27000 -vvvv -D checkpoint -W checkpoint" % client_ip)
            
            print "- wait for ip to take effect..."
            st_ip = time.time()
            while not ip_ready.get(vip, False):
                time.sleep(0.1)
            t = time.time() - st_ip; times["wait_ip_extra"] = t
            print "- Time: %.2g s" % t
            print "- live restore container"
            rt = time.time(); times["restore_rest"] = rt
            new_window("Restore - %s" % container, 
                       "runc --debug restore %s --image-path checkpoint --work-path checkpoint --bundle %s --lazy-pages %s" % (extensions, bundle_path, container))
            print "- tweak fw rules"
            wait_remove_drop_rules()
        et = time.time()
        times["restore_op"] = et - rt; times["restore_total"] = et - st; times["restore_end"] = time.time()
        print "- Restore time: %.2g s" % times["restore_op"] 
        return retvar
        
    @pyjsonrpc.rpcmethod
    def report_time(self, client_ts, client_sz):
        print "----------------------"
        print "migrate summary:"
        print "dump sizes:"; pprint.pprint(client_sz)
        print "client times:"; pprint.pprint(client_ts)
        print "server times:"; pprint.pprint(times)
        print "----------------------"
        print json.dumps(client_sz), json.dumps(client_ts), json.dumps(times)
       
svr = pyjsonrpc.ThreadingHttpServer(server_address=("0.0.0.0", 9000), RequestHandlerClass=MigrateService)
svr.allow_reuse_address = True   
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

