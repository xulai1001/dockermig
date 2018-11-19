#!/bin/bash
echo "- docker registry/experimental config..."
cp daemon.json /etc/docker/
echo "- sshd root access (PermitRootLogin)..."
gedit /etc/ssh/sshd_config
echo "- set root password..."
passwd
echo "- go path (hard-coded)..."
echo "PATH=\"/home/islab/go/bin:\$PATH\"" | tee -a /home/islab/.profile
echo "export GOPATH=/home/islab/go" | tee -a /home/islab/.profile
echo "export GOROOT=/usr/lib/go" | tee -a /home/islab/.profile
echo "- check .profile contents..."
gedit /home/islab/.profile
echo "- git config..."
read -n1
git config --global user.email xulai1001@gmail.com
git config --global user.name viktorxu
