import argparse
import json
import logging
import os
from typing import *
import sqlite3

import flask
from flask import g

from orm import LibraryId, FilePath, _Library, _Record


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler())

src_path = os.path.dirname(__file__)
with open(os.path.join(src_path, 'main.js'), 'r') as in_f:
    main_js = in_f.read()

with open(os.path.join(src_path, 'main.css'), 'r') as in_f:
    main_css = in_f.read()


class Library(_Library):
    @classmethod
    def create_table(cls):
        super().create_table()
        cur = cls._cursor()
        cur.execute(f'''INSERT INTO {cls.TABLE} (id, fields) VALUES (0, '[]')''')

    def children(self) -> List["Library"]:
        return self.list(parent_id=self.id)

    def tree(self, depth: Optional[int] = None) -> Dict:
        if depth is None:
            nxt_depth = None
        else:
            nxt_depth = depth - 1

        res = self.to_dict()

        if depth > 0:
            res["Library"] = []
            for child in self.children():
                res["Library"].append(child.tree(nxt_depth))

            res["Record"] = []
            for record in Record.list(parent_id=self.id):
                res["Record"].append(record.to_dict())

        return res


class Record(_Record):
    @classmethod
    def exists(cls, referrent: FilePath) -> bool:
        cur = cls._cursor()
        cur.execute(f"SELECT 1 FROM {cls.TABLE} WHERE referrent = ?", (referrent,))
        return bool(cur.fetchone())


def recur_ls(root: FilePath, name: str) -> Dict:
    res = {"name": name, "dirs": [], "files": []}
    scan = cast(Iterable[os.DirEntry], os.scandir(root))
    for direntry in scan:
        if direntry.is_dir():
            res["dirs"].append(recur_ls(direntry.path, direntry.name))
        else:
            if not Record.exists(direntry.path):
                res["files"].append(direntry.name)
    return res


class HardlinkerServer:
    def __init__(self, listen_root: FilePath, db_path: FilePath, host: str = '0.0.0.0', port: int = 4000):
        self.listen_root = listen_root
        self.db_path = db_path
        self.host = host
        self.port = port

        self.app = flask.Flask(__name__)
        self.app.before_request(self.before_request)
        self.app.after_request(self.after_request)
        self.app.route("/", methods=["GET"])(self.root)
        self.app.route("/tree", methods=["GET"])(self.list_unlinked)
        self.app.route("/list_library/<int:library_id>", methods=["GET"])(self.list_library)
        self.app.route("/library", methods=["PUT"])(self.put_library)
        self.app.route("/library/<int:library_id>", methods=["PATCH"])(self.patch_library)
        self.app.route("/record", methods=["PUT"])(self.put_record)

        self.app.route("/main.js", methods=["GET"])(self.main_js)
        self.app.route("/main.css", methods=["GET"])(self.main_css)
        self.app.route("/favicon.ico", methods=["GET"])(self.favicon)

    def before_request(self):
        db_exists = os.path.exists(self.db_path)
        g.sql_conn = sqlite3.connect(self.db_path)
        if not db_exists:
            Library.create_table()
            Record.create_table()

    def after_request(self, resp: flask.Response):
        conn: sqlite3.Connection = g.sql_conn
        conn.commit()
        return resp

    def serve(self):
        self.app.run(self.host, self.port, debug=True)

    def root(self) -> str:
        return '<html><head><link rel="stylesheet" href="/main.css"/></head><body><div id="main"/><script src="/main.js"></script></body></html>'

    def main_css(self) -> str:
        return main_css

    def main_js(self) -> str:
        return main_js

    def favicon(self) -> str:
        return 'hi2u'

    def list_unlinked(self) -> dict:
        return recur_ls(self.listen_root, self.listen_root)

    def list_library(self, library_id: LibraryId) -> str:
        return json.dumps(Library.get(library_id).tree(depth=1))

    def put_library(self) -> str:
        data = flask.request.json
        library = Library.new(**data)
        library.save()
        return json.dumps(library.to_dict())

    def patch_library(self, library_id: LibraryId) -> str:
        data = flask.request.json
        library = Library.get(library_id)
        library.update(**data)
        library.save()
        return json.dumps(library.to_dict())

    def put_record(self) -> str:
        data = flask.request.json
        logger.info("LINK!", data)
        record = Record.new(**data)
        library = Library.get(record.parent_id)

        fmt = library.format
        fname = fmt.format(**record.attributes)
        fpath = os.path.join(library.location, fname)
        info = {
            "src": record.referrent,
            "fmt": fmt,
            "attrs": record.attributes,
            "fname": fname,
            "location": library.location,
            "fpath": fpath,
        }
        logger.info(info)

        dirname = os.path.dirname(fpath)
        os.makedirs(dirname, exist_ok=True)
        os.link(record.referrent, fpath)
        logger.info("Success!")

        record.save()
        return json.dumps(record.to_dict())


def cli_main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--listen-root')
    parser.add_argument('--db-path')
    parser.add_argument('--host', default='0.0.0.0')
    parser.add_argument('--port', type=int, default=4000)
    args = parser.parse_args()

    server = HardlinkerServer(args.listen_root, args.db_path, args.host, args.port)
    server.serve()


if __name__ == '__main__':
    cli_main()
else:
    listen_root = FilePath(os.environ["LISTEN_ROOT"])
    db_path = FilePath(os.environ["DB_PATH"])
    server = HardlinkerServer(listen_root, db_path)
    app = server.app
