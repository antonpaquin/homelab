#! /bin/bash

initdb -D /data/new -U postgres

cd /data

pg_upgrade \
  -b /usr/lib/postgresql/11/bin \
  -B /usr/lib/postgresql/14/bin \
  -d /data/old \
  -D /data/new