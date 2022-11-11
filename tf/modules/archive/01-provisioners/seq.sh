#! /bin/bash

SRC_DIR="$(dirname "${BASH_SOURCE[0]}")"
cd "$SRC_DIR"

set -ex

pushd 00-Rook
terraform apply
popd

pushd 01-Rook
terraform apply
popd

pushd 02-Rook
terraform apply
popd

while sleep 1; do
  CJSON="$(kubectl get cm/rook-ceph-csi-config -n rook -o json | jq -r .data.\"csi-cluster-config-json\")"
  CLEN="$(echo "$CJSON" | jq -r '. | length')"
  if [[ "$CLEN" == "1" ]]; then
    break
  fi
done

pushd 03-Rook
terraform apply
popd
