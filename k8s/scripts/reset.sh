#! /bin/bash

set -x

ssh reimu-00 <<EOF
    set -x
    sudo umount -l "/var/lib/kubelet/plugins/kubernetes.io~local-volume/volumeDevices/"*/*
    sudo kubeadm reset -f
    sudo rm -r /etc/cni/net.d/
    sudo systemctl restart crio
EOF

# Anton: does cirno need that umount line?
ssh cirno <<EOF
    set -x
    sudo kubeadm reset -f
    sudo rm -r /etc/cni/net.d/
    sudo systemctl restart crio
EOF

ssh hakurei <<EOF
    set -x
    sudo kubeadm reset -f
    sudo rm -r /etc/cni/net.d/
    sudo systemctl restart crio
EOF
