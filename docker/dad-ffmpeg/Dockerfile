FROM ubuntu:latest

RUN \
    apt update \
 && DEBIAN_FRONTEND=noninteractive \
    TZ=US/Pacific \
    apt install -y \
        apt-transport-https \
        cifs-utils \
        curl \
        dnsutils \
        ffmpeg \
        git \
        gnupg \
        htop \
        net-tools \
        openssh-server \
        python3-pip \
        sudo \
        vim

RUN mkdir -p /run/sshd
ADD sudoers /etc/sudoers

RUN pip3 install configargparse

RUN \
    curl -s https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key add - \
 && echo "deb https://apt.kubernetes.io/ kubernetes-xenial main" | tee -a /etc/apt/sources.list.d/kubernetes.list \
 && apt update \
 && apt install -y kubectl

RUN useradd \
    -m \
    -s /bin/bash \
    tom \
 && yes "tom" | passwd tom \
 && usermod -a -G sudo tom

ADD entrypoint.sh /entrypoint.sh
ENTRYPOINT /entrypoint.sh
