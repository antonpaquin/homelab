#! go into the console and type it, username is root/root

systemctl start sshd
useradd -m user
yes 'user' | passwd user
ifconfig  # get ip, add it to ssh config, go to next step

# step1 will need typing in passwords initially: user, then root
# after that should be all automatic
