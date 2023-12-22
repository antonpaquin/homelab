#! /bin/bash

set -e

if [[ "$1" == "" ]]; then
    echo "Usage: $0 <hostname> <cidr>"
    exit 1
fi

if [[ "$2" == "" ]]; then
    echo "Usage: $0 <hostname> <cidr>"
    exit 1
fi

HOSTNAME="$1"
CIDR="$2"

cd /home/anton/nebula
./nebula-cert sign \
    -ca-crt /etc/nebula/ca.crt \
    -ca-key /etc/nebula/ca.key \
    -name "$HOSTNAME" \
    -ip "$CIDR"

mkdir /home/anton/nebula/certs/"$HOSTNAME"
mv "$HOSTNAME.crt" /home/anton/nebula/certs/"$HOSTNAME"/host.crt
mv "$HOSTNAME.key" /home/anton/nebula/certs/"$HOSTNAME"/host.key
cp /etc/nebula/ca.crt /home/anton/nebula/certs/"$HOSTNAME"/ca.crt

cd /home/anton/nebula/certs/"$HOSTNAME"
cp /home/anton/nebula/default_config.yaml ./nebula.yaml
zip -r9 /home/anton/nebula/certs_zip/"$HOSTNAME".zip .
rm ./nebula.yaml