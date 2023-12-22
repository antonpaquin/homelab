#! /bin/bash

set -e

if [[ "$JELLYFIN_DB_TEMPLATE" == "" ]]; then
    echo "JELLYFIN_DB_TEMPLATE is not set"
    exit 1
fi

if [[ "$JELLYFIN_DB_HOST" == "" ]]; then
    echo "JELLYFIN_DB_HOST is not set"
    exit 1
fi

init_setup() {
    rsync -r "$JELLYFIN_DB_TEMPLATE" "$JELLYFIN_DB_HOST"
}

periodic_refresh() {
    while true; do
        sleep 1m
        rsync -r "$JELLYFIN_DB_HOST" "$JELLYFIN_DB_TEMPLATE"
    done
}

init_setup
periodic_refresh &

exec /jellyfin/jellyfin "$@"