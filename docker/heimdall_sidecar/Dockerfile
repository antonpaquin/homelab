FROM python:3.9.6-alpine

RUN pip3 install requests

ADD main.py /opt/main.py
ADD entrypoint.sh /entrypoint.sh
ENTRYPOINT /entrypoint.sh
