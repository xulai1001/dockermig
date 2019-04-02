#!/bin/bash
container=$1
server=$2
vip=$3
migrate_script=./migrate.py

#echo "- stop keepalived..."
#sudo killall keepalived

#echo "- wait 3 sec..."
#sleep 3

#echo "- start keepalived..."
#sudo keepalived -d
# gnome-terminal -t "Keepalived debug" -- tail -f /var/log/syslog

echo "- enter work dir for $1..."
cd ../containers/$1/bundle

echo "- start container"
sudo gnome-terminal -t "Container - $1" -- /usr/local/sbin/runc run $1

echo "- wait 5 sec..."
sleep 5
echo "- test service & floating ip"
if [ $container = ubuntu-islab ]; then
    vip=192.168.100.100
    ssh root@$vip -p 8122 uname -a
    gnome-terminal -t "SSH Connection" -- ssh root@$vip -p 8122
elif [ $container = flv-live ]; then
    vip=192.168.100.71
    gnome-terminal -- smplayer http://$vip:7001/demo/demo.flv
fi
echo "- press key to migrate $container to $server..."
read -n1

sudo $migrate_script $container $server $vip


