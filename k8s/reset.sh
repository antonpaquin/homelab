#! /bin/bash

set -ex

ssh reimu-00 <<EOF
    sudo kubeadm reset -f
    sudo rm -r /etc/cni/net.d/
    sudo systemctl restart docker
    sudo reboot
EOF

ssh hakurei <<EOF
    sudo kubeadm reset -f
    sudo rm -r /etc/cni/net.d/
    sudo systemctl restart docker
EOF
