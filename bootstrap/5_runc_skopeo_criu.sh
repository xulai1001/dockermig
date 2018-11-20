#!/bin/bash
pushd ~/src
git clone https://github.com/containers/skopeo
gopm bin github.com/opencontainers/runc
git clone https://github.com/checkpoint-restore/criu

echo "- skopeo ..."
read -n1 -p "press key..."
pushd skopeo
make binary
read -n1 -p "press key..."
sudo make install
popd

echo "- criu ..."
pushd criu
read -n1 -p "press key..."
make
read -n1 -p "press key..."
sudo make install
