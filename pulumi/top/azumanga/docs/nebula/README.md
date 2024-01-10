# Nebula

Nebula is a vpn that you can use to access the cluster from outside the house.

## How to install

1) Ask Anton to send you a config file

2) Go to https://github.com/slackhq/nebula/releases and download the right version for your OS

3) The github nebula release comes with two binary files, `nebula` and `nebula-cert`. 
Extract the one called `nebula` to your `/bin` directory

```bash
unzip nebula-darwin.zip
sudo mv nebula /bin/nebula
```

4) The config files tell nebula how to connect. We need to extract them to /etc/nebula/

```bash
unzip my_config.zip
sudo mkdir -p /etc/nebula
sudo mv host.key host.crt ca.crt nebula.yaml /etc/nebula/
```

5) Now you are installed

## How to use

1) You need to start nebula in a terminal and run it in the background to connect.
Run this in a terminal

```bash
sudo nebula -config /etc/nebula/nebula.yaml
```

It may ask for your laptop's password to let you run this command as root.

You should see log lines with some blue text scrolling by. 
Leave the terminal running in the background. 
You are connected as long as the program is running.

2) Now you can connect to the cluster. Go to http://192.168.100.102:12020

## Anton: how to generate configs

```bash
    ssh gateway
    su anton
    cd /home/anton/nebula
    cat ip_reservation.txt  # pick an ip
    ./gen_cert.sh <name> 192.168.100.xyz/24
```
