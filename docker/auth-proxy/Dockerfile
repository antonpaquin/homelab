FROM python:3.9.6-buster

RUN pip3 install cryptography flask gunicorn pyjwt requests
ADD authfail_img /opt/authproxy/authfail_img/
ADD main.py entrypoint.sh /opt/authproxy/

ENTRYPOINT ["/opt/authproxy/entrypoint.sh"]

