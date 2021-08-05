FROM python:3.9.6-alpine

RUN pip3 install gunicorn flask
ADD main.py orm.py main.js main.css entrypoint.sh /opt/hardlinker/

ENTRYPOINT ["/opt/hardlinker/entrypoint.sh"]
