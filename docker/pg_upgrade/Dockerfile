FROM postgres:11.16-bullseye as v11
FROM postgres:14.4-bullseye

COPY --from=v11 /usr/lib/postgresql/11 /usr/lib/postgresql/11
COPY --from=v11 /usr/share/postgresql/11 /usr/share/postgresql/11

RUN \
    useradd -u 1000 user \
 && mkdir /data \
 && chown -R 1000:1000 /data

COPY entrypoint.sh /entrypoint.sh
