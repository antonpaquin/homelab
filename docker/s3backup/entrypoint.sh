#! /bin/bash

hashbak backup \
  "$@" \
  --salt-hex $HASH_SALT \
  --key-hex $AES_KEY
