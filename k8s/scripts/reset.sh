#! /bin/bash

set -x

# zfs0: I think something screwy was going on with last kubeadm reset?
# don't play around with things that might rm -rf
ssh reimu-00 <<EOF
    set -x
    sudo umount -l "/var/lib/kubelet/plugins/kubernetes.io~local-volume/volumeDevices/"*/*
    sudo zfs umount zfs0
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
