#! /usr/bin/env python3

import json
import logging

import flask

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG)

app = flask.Flask(__name__)


@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def root(path) -> flask.Response:
    request = flask.request
    resp = json.dumps({
        'url': request.url,
        'path': path,
        'headers': dict(request.headers),
        'args': request.args,
        'form': request.form,
        'data': request.data.decode('utf-8'),
        'method': request.method,
    })
    logger.info(resp)
    return flask.Response(resp, 200)


if __name__ == '__main__':
    app.run('0.0.0.0', 3000)
