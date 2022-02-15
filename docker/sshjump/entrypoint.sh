#! /bin/bash

ssh -o StrictHostKeyChecking=no -R "0.0.0.0:80:$DEST:80" -R "0.0.0.0:443:$DEST:443" -N sshjump