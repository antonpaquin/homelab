FROM antonpaquin/shell:latest

RUN apt install -y ssh
COPY entrypoint.sh /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]