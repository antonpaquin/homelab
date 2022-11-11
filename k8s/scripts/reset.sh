#! /bin/bash

set -x

ssh reimu-00 <<EOF
    set -x
    sudo umount -l "/var/lib/kubelet/plugins/kubernetes.io~local-volume/volumeDevices/"*/*
    sudo kubeadm reset -f
    sudo rm -r /etc/cni/net.d/
    sudo systemctl restart docker
    sudo systemctl restart containerd
    sudo ctr -n k8s.io c rm \$(sudo ctr -n k8s.io c ls -q)
    sudo reboot
EOF

# Anton: does cirno need that umount line?
ssh cirno <<EOF
    set -x
    sudo kubeadm reset -f
    sudo rm -r /etc/cni/net.d/
    sudo systemctl restart docker
    sudo systemctl restart containerd
    sudo ctr -n k8s.io c rm \$(sudo ctr -n k8s.io c ls -q)
    sudo reboot
EOF

ssh hakurei <<EOF
    set -x
    sudo kubeadm reset -f
    sudo rm -r /etc/cni/net.d/
    sudo systemctl restart docker
    sudo systemctl restart containerd
    sudo ctr -n k8s.io c rm \$(sudo ctr -n k8s.io c ls -q)
EOF
