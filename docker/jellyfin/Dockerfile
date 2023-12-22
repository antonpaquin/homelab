FROM jellyfin/jellyfin:20231120.3-unstable

RUN apt update && apt install -y rsync

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT [ "/entrypoint.sh" ]