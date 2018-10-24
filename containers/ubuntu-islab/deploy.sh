#!/bin/bash
cd ~
mkdir -p src
mkdir -p .ssh
cd .deploy
cp id_rsa.pub ~/.ssh/authorized_keys

# deploy test
echo "-- deploy test --"
tree -a ~/
echo "- authorized_keys is:"
cat ~/.ssh/authorized_keys
echo "- ubuntu version:"
cat /etc/lsb-release
