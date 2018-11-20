#!/bin/bash
sudo apt install -y vim openssh-server tree pv curl ruby python gcc g++ build-essential golang git gedit lrzsz lxc criu \
                go-md2man asciidoc xmlto
sudo apt install -y libseccomp-dev libprotobuf-dev libprotobuf-c0-dev protobuf-c-compiler protobuf-compiler python-protobuf pkg-config \
                python-ipaddress libbsd0 iproute2 libcap-dev libnet1-dev libaio-dev python-yaml libnl-3-dev python-future texlive-latex-base

echo "- install docker..."
curl -sSL https://get.daocloud.io/docker |sh
echo "- add islab to docker group...(hard coded)"
sudo usermod -aG docker islab

