FROM python:3.9.6-alpine

RUN pip3 install kubernetes pyyaml

ADD main.py /opt/pv-saver/main.py

ENTRYPOINT ["/opt/pv-saver/main.py"]
