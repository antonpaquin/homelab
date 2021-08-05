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

pushd 02-application
terraform apply
popd
