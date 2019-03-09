#!/usr/bin/python
import socket, sys, select
import time, os, shutil, subprocess, commands
import contextlib
import distutils.util
import pyjsonrpc, socket

container = sys.argv[1]
dest = sys.argv[2]
lazy = True
pre = True
remote_base_path = "/home/islab/src/dockermig/containers/%s/" % container
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

def run_cmd_timed(cmd):
    global retvar
    print "- " + cmd
    st = time.time()
    retvar = os.system(cmd)
    exit_on_error()
    print "- time: %.2g s" % (time.time() - st)

# workers
def pre_dump():
    print "- start predump..."
    run_cmd_timed("sudo runc checkpoint --tcp-established --pre-dump --image-path predump %s" % container)
    retvar, psize = commands.getstatusoutput("du -hs predump")
    print "- PRE-DUMP size: %s" % psize
    
def checkpoint_dump():    
    run_cmd_timed("sudo runc --debug checkpoint --tcp-established --shell-job --file-locks --image-path checkpoint --parent-path %s/bundle/predump %s" % (remote_base_path, container))
    os.system("unlink checkpoint/parent") # remove symlink to parent. will be restored in dest host
    ret, csize = commands.getstatusoutput("du -hs checkpoint")
    print "- CHECKPOINT size: %s" % csize

def lazy_dump():
    global retvar
    cmd = """gnome-terminal -t 'CRIU page server' -- /home/islab/src/dockermig/scripts/run.sh runc --debug checkpoint --tcp-established --shell-job --file-locks --image-path checkpoint --parent-path %s/bundle/predump --shell-job --lazy-pages --page-server 0.0.0.0:27000 --status-fd copy_pipe %s""" % (remote_base_path, container)
    if os.path.exists("copy_pipe"):
        os.unlink("copy_pipe")
    os.mkfifo("copy_pipe")
    
    print "- " + cmd
    st = time.time()
    os.system(cmd)
    cp = os.open("copy_pipe", os.O_RDONLY)
    x = os.read(cp, 1) # wait here
    if x == "\0":
        print "- ready for lazy page copy..."
    print "- time: %.2g s, retvar: %d" % (time.time() - st, retvar)
    retvar, csize = commands.getstatusoutput("du -hs checkpoint")
    print "- CHECKPOINT size: %s" % csize

def send_rootfs():
    global remote_base_path
    print "- send ROOTFS to %s:%s/rootfs" % (dest, remote_base_path)
    run_cmd_timed("rsync -aqz rootfs %s:%s" % (dest, remote_base_path))
    os.system("scp config.json %s:%s" % (dest, remote_base_path))
    
def send_pre_dump():
    global remote_base_path
    print "- send PRE-DUMP to %s:%s" % (dest, remote_base_path)
    run_cmd_timed("rsync -aqz predump %s:%s" % (dest, remote_base_path))
    
def send_checkpoint():
    global remote_base_path
    print "- send CHECKPOINT to %s:%s" % (dest, remote_base_path)
    run_cmd_timed("rsync -aqz checkpoint %s:%s" % (dest, remote_base_path))
    
def stop_kad():
    print "- stop keepalived..."
    run_cmd_timed("killall keepalived")
    
if __name__ == "__main__":
    ip = get_ip()
    print "- host ip: %s" % ip
    cli = pyjsonrpc.HttpClient(url = "http://%s:9000/jsonrpc" % dest)
    os.system("rm -rf predump checkpoint")
    remote_base_path = cli.prepare(ip, container)
    print "- remote path: %s:%s" % (dest, remote_base_path)
    
    send_rootfs()
    pre_dump()
    send_pre_dump()
    checkpoint_dump()
#    lazy_dump()
    send_checkpoint()
    stop_kad()
    cli.restore(container)
#    cli.lazy_restore(ip, container)
    
