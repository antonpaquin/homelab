#! /bin/bash

SRC_DIR="$(dirname "${BASH_SOURCE[0]}")"
cd "$SRC_DIR"

set -ex

pushd 00-init
terraform apply
popd

pushd 01-provisioners
./seq.sh
popd

pushd 02-remote
terraform apply
popd

pushd 03-application
terraform apply
popd

pushd 04-auth
terraform apply
popd
