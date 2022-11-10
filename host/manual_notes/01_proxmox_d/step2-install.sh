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
        sudo pacman -S --noconfirm htop patch vim
    
        sudo systemctl enable crio
        sudo systemctl start crio
        sudo systemctl enable kubelet

        sudo kubeadm config images pull --cri-socket=unix:///var/run/crio/crio.sock
EOF
