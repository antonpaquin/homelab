FROM ubuntu:latest

RUN useradd ubuntu
RUN usermod -a -G sudo ubuntu
RUN apt update
RUN apt install -y sudo jq

ADD sudoers /etc/sudoers
