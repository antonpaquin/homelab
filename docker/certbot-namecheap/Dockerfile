FROM certbot/certbot

RUN apk add curl jq
RUN pip install kubernetes

COPY namecheap-plugin /opt/namecheap-plugin
RUN pip install -e /opt/namecheap-plugin

COPY upload_certs.py /opt/upload_certs.py

COPY entrypoint.sh /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
