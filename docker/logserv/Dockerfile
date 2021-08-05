FROM python:3.9.6-alpine

RUN pip3 install flask

ADD main.py /opt/logserv/main.py

ENTRYPOINT ["/opt/logserv/main.py"]
