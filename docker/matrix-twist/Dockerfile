FROM python:3.9.6-buster

RUN pip3 install flask gunicorn requests

COPY src /opt/matrix-twist

ENTRYPOINT ["/opt/authproxy/entrypoint.sh"]

