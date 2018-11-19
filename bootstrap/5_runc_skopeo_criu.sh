#!/bin/bash
pushd ~/src
git clone https://github.com/containers/skopeo
git clone https://github.com/opencontainers/runc
git clone https://github.com/checkpoint-restore/criu

echo "- skopeo ..."
read -n1
pushd skopeo
make binary
read -n1
sudo make install
popd

echo "- runc ..."
read -n1
pushd runc
make
read -n1
sudo make install
popd

echo "- criu ..."
read -n1
make
read -n1
sudo make install
