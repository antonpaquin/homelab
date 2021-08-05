#! /bin/bash

set -ex

SRC_DIR="$(dirname "${BASH_SOURCE[0]}")"
cd "$SRC_DIR"

TARGET="$(basename "$1")"
if [[ ! -d "./$TARGET" ]]; then
  echo "Did not find $TARGET"
  exit 1
fi

tar -czvf $TARGET.tar.gz $TARGET
scp $TARGET.tar.gz util:$TARGET.tar.gz
rm $TARGET.tar.gz

ssh util <<EOF
  set -ex
  if [[ -d $TARGET ]]; then
    rm -r $TARGET
  fi
  tar -xzvf $TARGET.tar.gz
  rm $TARGET.tar.gz
  pushd $TARGET
  make
  popd
  rm -r $TARGET
EOF
