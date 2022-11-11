#! /bin/bash

FNAME="deadman.txt"

while sleep 5; do
  ssh reimu touch "$FNAME"
done