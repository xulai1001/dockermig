#!/bin/bash
cname=$1
mkdir -p oci bundle
skopeo copy docker-daemon:$cname:latest oci:oci/:$cname
oci-image-tool create --ref name=$cname oci bundle
rm -rf oci
pushd bundle
mv config.json conf
runc spec
echo "- manually merge config specs..."
gedit config.json conf
