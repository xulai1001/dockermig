#!/usr/bin/python
import socket, sys, select
import time, os, shutil, subprocess, commands
import contextlib
import distutils.util
import pyjsonrpc, socket
from pprint import pprint

container = sys.argv[1]
dest = sys.argv[2]
vip = ""
if len(sys.argv)>3: vip = sys.argv[3]
lazy = True
pre = True
remote_base_path = "/home/islab/src/dockermig/containers/%s/" % container
status_server = "%s:9001" % dest
times = {}
sizes = {}
# bundle: original container
# predump: predump image
# checkpoint: checkpoint image

# helpers
# https://blog.csdn.net/u013314786/article/details/78962103
def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("baidu.com", 80))
    ip = s.getsockname()[0]
    s.close()
    return ip

# https://stackoverflow.com/questions/6194499/pushd-through-os-system
#@contextlib.contextmanager
#def pushd(d):
#    last_dir = os.getcwd()
#    os.chdir(d)
#    print "> entering %s" % d
#    yield
#    os.chdir(last_dir)

retvar = 0

def exit_on_error():
    global retvar
    if retvar != 0:
        print "- error: %d, exiting..." % retvar
        sys.exit(retvar)  

def run_cmd_timed(cmd, tag=""):
    global retvar
    print "- " + cmd
    st = time.time()
    retvar = os.system(cmd)
    exit_on_error()
    t = time.time() - st
    print "- time: %.2g s" % t
    if len(tag)>0: times[tag] = t
    
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
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   
# workers
extensions = "--tcp-established --shell-job --file-locks"

def pre_dump():
    print "- start predump..."
    run_cmd_timed("sudo runc checkpoint %s --pre-dump --image-path predump %s" % (extensions, container), "predump")
    print "- PRE-DUMP size: %s" % getsize("predump")
    
def checkpoint_dump():    
    run_cmd_timed("sudo runc --debug checkpoint %s --image-path checkpoint --parent-path %s/bundle/predump %s" % (extensions, remote_base_path, container), "checkpoint")
    os.system("unlink checkpoint/parent") # remove symlink to parent. will be restored in dest host
    print "- CHECKPOINT size: %s" % getsize("checkpoint")

def lazy_dump():
    global retvar
#    cmd = """gnome-terminal -t 'CRIU page server' -- /home/islab/src/dockermig/scripts/run.sh runc --debug checkpoint --tcp-established --shell-job --file-locks --image-path checkpoint --parent-path %s/bundle/predump --shell-job --lazy-pages --page-server 0.0.0.0:27000 --status-fd copy_pipe %s""" % (remote_base_path, container)
    cmd = """runc --debug checkpoint %s \\
                  --image-path checkpoint --parent-path %s/bundle/predump \\
                  --lazy-pages --page-server 0.0.0.0:27000 --status-fd copy_pipe \\
                  %s""" % (extensions, remote_base_path, container)
    if os.path.exists("copy_pipe"):
        os.unlink("copy_pipe")
    os.mkfifo("copy_pipe")
    
    st = time.time()
    new_window("CRIU page server", cmd)
    cp = os.open("copy_pipe", os.O_RDONLY)
    x = os.read(cp, 1) # wait here
    if x == "\0":
        print "- ready for lazy page copy..."
        
    t = time.time() - st; times["checkpoint"] = t
    print "- time: %.2g s, retvar: %d" % (t, retvar)
    print "- CHECKPOINT size: %s" % getsize("checkpoint")
    print_fw()

def send_rootfs():
    global remote_base_path
    print "- send ROOTFS to %s:%s/rootfs" % (dest, remote_base_path)
    run_cmd_timed("rsync -aqz rootfs %s:%s" % (dest, remote_base_path), "rootfs_send")
    os.system("scp config.json %s:%s" % (dest, remote_base_path))
    
def send_pre_dump():
    global remote_base_path
    print "- send PRE-DUMP to %s:%s" % (dest, remote_base_path)
    run_cmd_timed("rsync -aqz predump %s:%s" % (dest, remote_base_path), "predump_send")
    
def send_checkpoint():
    global remote_base_path
    print "- send CHECKPOINT to %s:%s" % (dest, remote_base_path)
    run_cmd_timed("rsync -aqz checkpoint %s:%s" % (dest, remote_base_path), "checkpoint_send")
    
def stop_kad():
    print "- stop keepalived..."
    run_cmd_timed("killall keepalived")
    
if __name__ == "__main__":
    ip = get_ip()
    print "- host ip: %s, service ip (vip): %s" % (ip, vip)
    cli = pyjsonrpc.HttpClient(url = "http://%s:9000/jsonrpc" % dest)
    status_cli = pyjsonrpc.HttpClient(url = "http://%s/jsonrpc" % status_server)
    
    # tell the status server that we have the container now
    status_cli.set_container(container, ip)
    
    os.system("rm -rf predump checkpoint")
    
    times["migrate_start"] = time.time()
    remote_base_path = cli.prepare(ip, container)
    print "- remote path: %s:%s" % (dest, remote_base_path)
    
    send_rootfs()
    pre_dump()
    send_pre_dump()
#    checkpoint_dump()

    # tell the status server that we are sending the container now
    status_cli.set_container(container, dest)
    cli.move_ip(vip)

    times["migrate_stop"] = time.time()
    lazy_dump()

    send_checkpoint()
   # stop_kad()
#    cli.restore(container)
    cli.lazy_restore(ip, container, vip)
    times["migrate_end"] = time.time()
    
    print "- Times:"
    pprint(times)
    print "- Sizes:"
    pprint(sizes)
    cli.report_time(times, sizes)
    
    
