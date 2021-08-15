FROM ubuntu:latest

RUN useradd ubuntu
RUN usermod -a -G sudo ubuntu
RUN apt update
RUN apt install sudo

ADD sudoers /etc/sudoers
