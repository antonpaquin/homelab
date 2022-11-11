#! /bin/bash

if [[ "$CONFIG" == "" ]]; then
  CONFIG='{"ports": [80, 443]}'
fi

RFLAGS=""

for PORT in $(echo "$CONFIG" | jq -r '.ports | join("\n")'); do
  RFLAGS="$RFLAGS -R 0.0.0.0:$PORT:$DEST:$PORT"
done

ssh -o StrictHostKeyChecking=no $RFLAGS -N sshjump