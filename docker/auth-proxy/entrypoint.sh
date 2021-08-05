#! /usr/bin/env sh

cd /opt/authproxy/
gunicorn -b "$APP_HOST:$APP_PORT" main:app