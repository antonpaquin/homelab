FROM python:3.10.5-bullseye

RUN pip3 install cryptography boto3

COPY src /opt/hashbak
RUN cd /opt/hashbak \
 && pip install -e .

COPY entrypoint.sh /opt/hashbak/entrypoint.sh

WORKDIR /opt/hashbak

ENTRYPOINT ["/opt/hashbak/entrypoint.sh"]

