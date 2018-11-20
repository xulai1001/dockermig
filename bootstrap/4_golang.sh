#!/bin/bash
echo "GOPATH: $GOPATH"
go get -u -v github.com/gpmgo/gopm
pushd ~/.gopm
ln -s $GOPATH/src repos
popd

echo "- install go packages..."
read -n1 -p"press key..."
gopm get golang.org/x/sys/unix
gopm get github.com/urfave/cli
gopm get github.com/sirupsen/logrus
gopm get github.com/pkg/errors
gopm get github.com/containerd/console
gopm get github.com/coreos/go-systemd/activation
gopm get github.com/docker/go-units
gopm get github.com/opencontainers/runtime-spec
gopm get github.com/opencontainers/image-spec
gopm get github.com/opencontainers/runc/libcontainer

echo "- install oci-image-tool..."
read -n1 -p"press key..."
gopm bin github.com/opencontainers/image-tools/cmd/oci-image-tool

echo "- build oci-runtime-spec..."
read -n1 -p"press key..."
docker pull vbatts/pandoc
cd $GOPATH/src/github.com/opencontainers/runtime-spec/
make
