#! /usr/bin/env bash

set -ex

ssh reimu-00 <<EOF
  set -ex
  sudo rm -rf /storage/meta
  sudo mkdir /storage/meta
  sudo dd if=/dev/zero of=/dev/sdb bs=1M count=20
  sudo dd if=/dev/zero of=/dev/sdc bs=1M count=20
  sudo dd if=/dev/zero of=/dev/sdd bs=1M count=20
EOF

