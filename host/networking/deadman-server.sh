#! /bin/bash

FNAME="deadman.txt"
BAK_NAME="interfaces.bak"

if [[ "$UID" != 0 ]]; then
  echo "run as root" >2
  exit 1
fi

while sleep 5; do
  if [[ $(expr $(date +%s) - $(stat -c '%Y' $FNAME)) -ge 10 ]]; then
    echo "Deadman failed, restarting networking"
    cp "$BAK_NAME" /etc/network/interfaces
    systemctl restart networking
  fi
done