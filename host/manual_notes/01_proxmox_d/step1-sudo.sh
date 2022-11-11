#! /bin/bash


if [[ "$1" == "" ]]; then
	echo "need arg1" 1>&2
	exit 1
fi
TARGET="$1"

cd -- "$( dirname -- "${BASH_SOURCE[0]}" )"

set -ex

SSHKEY="$(cat assets/ssh.pub)"

SUDO_SCRIPT="$(cat <<EOF
set -ex
pacman -Sy
pacman -S --noconfirm archlinux-keyring
pacman -Syu --noconfirm 
pacman -S --noconfirm sudo
groupadd sudo
usermod -a -G sudo user
echo '%sudo ALL=(ALL:ALL) NOPASSWD: ALL' >> /etc/sudoers
mkdir ~/.ssh
echo '$SSHKEY' >> ~/.ssh/authorized_keys
EOF
)"

S_B64="$(echo "$SUDO_SCRIPT" | base64 | tr -d '\n')"

ssh $TARGET su -c "bash -c \"\$(echo $S_B64 | base64 -d)\""

ssh $TARGET <<EOF
	set -ex
        sudo systemctl enable sshd
EOF

set +e
ssh $TARGET sudo reboot
set -e
