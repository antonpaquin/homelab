FROM python:3.9.6-buster

RUN pip3 install cryptography flask gunicorn pyjwt requests
COPY api_jwk.py.patch /root/api_jwk.py.patch
RUN patch /usr/local/lib/python3.9/site-packages/jwt/api_jwk.py < /root/api_jwk.py.patch

ADD authfail_img /opt/authproxy/authfail_img/
ADD main.py entrypoint.sh /opt/authproxy/

ENTRYPOINT ["/opt/authproxy/entrypoint.sh"]

