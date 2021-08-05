#! /usr/bin/env sh

cd /opt/hardlinker/
gunicorn -b "$APP_HOST:$APP_PORT" main:app