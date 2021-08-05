FROM python:3.9.6-buster

RUN pip3 install cryptography flask gunicorn pyjwt requests
ADD main.py entrypoint.sh /opt/authproxy/

ENTRYPOINT ["/opt/authproxy/entrypoint.sh"]

