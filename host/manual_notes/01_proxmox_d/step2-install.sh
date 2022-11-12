#! /bin/bash

cd -- "$( dirname -- "${BASH_SOURCE[0]}" )"

if [[ "$1" == "" ]]; then
        echo "need arg1" 1>&2
        exit 1
fi

TARGET="$1"

if [[ "$TARGET" == "reimu-00" ]]; then
        NEEDS_ZFS=1
else
        NEEDS_ZFS=
fi


set -ex

ssh $TARGET <<EOF
        set -ex
        sudo systemctl enable sshd
        sudo hostnamectl hostname $TARGET
EOF

if [[ $NEEDS_ZFS ]]; then
        # Create zfs pools: 
        # sudo zpool create -f -m /storage/root/ zfs0 raidz scsi-0QEMU_QEMU_HARDDISK_drive-scsi1 scsi-0QEMU_QEMU_HARDDISK_drive-scsi2 scsi-0QEMU_QEMU_HARDDISK_drive-scsi3
        scp assets/archzfs.conf $TARGET:/home/user/
        ssh $TARGET <<EOF
                set -ex
                sudo bash -c 'cat archzfs.conf >> /etc/pacman.conf'
                sudo pacman -Syu --noconfirm
                sudo pacman -Sy --noconfirm zfs-linux
EOF
        set +e
        ssh $TARGET sudo reboot
        set -e
	sleep 1
        sshwait $TARGET -q
	sleep 1

        ssh $TARGET <<EOF
                set -ex
                sudo modprobe zfs
                sudo mkdir -p /storage/root
                sudo zpool import zfs0
                sudo zpool set cachefile=/etc/zfs/zpool.cache zfs0

                sudo systemctl enable zfs-import-cache.service
                sudo systemctl start zfs-import-cache.service
                sudo systemctl enable zfs-import.target
                sudo systemctl enable zfs-mount.service
                sudo systemctl start zfs-mount.service
                sudo systemctl enable zfs.target
EOF

        set +e
        ssh $TARGET sudo reboot
        set -e
	sleep 1
        sshwait $TARGET -q
	sleep 1
fi

ssh $TARGET <<EOF
        set -ex
        sudo pacman -S --noconfirm kubelet kubeadm kubectl cri-o
        sudo pacman -S --noconfirm htop patch vim nfs-utils
    
        sudo systemctl enable crio
        sudo systemctl start crio
        sudo systemctl enable kubelet

        sudo kubeadm config images pull --cri-socket=unix:///var/run/crio/crio.sock
EOF


# TODO: if cilium works, then install the cli tool here
# CILIUM_CLI_VERSION=$(curl -s https://raw.githubusercontent.com/cilium/cilium-cli/master/stable.txt)
# CLI_ARCH=amd64
# if [ "$(uname -m)" = "aarch64" ]; then CLI_ARCH=arm64; fi
# curl -L --fail --remote-name-all https://github.com/cilium/cilium-cli/releases/download/${CILIUM_CLI_VERSION}/cilium-linux-${CLI_ARCH}.tar.gz{,.sha256sum}
# sha256sum --check cilium-linux-${CLI_ARCH}.tar.gz.sha256sum
# sudo tar xzvfC cilium-linux-${CLI_ARCH}.tar.gz /usr/local/bin
# rm cilium-linux-${CLI_ARCH}.tar.gz{,.sha256sum}

# TODO also apparently arch+crio+cilium requires a config file? see arch wiki https://wiki.archlinux.org/title/CRI-O
# /etc/crio/crio.conf.d/00-plugin-dir.conf
# [crio.network]
# plugin_dirs = [
#   "/opt/cni/bin/",
# ]
# Then a systemctl restart crio
