import json
import sqlite3
from typing import Optional, Any
from flask import g

class LibraryId(int):
    pass

class RecordId(int):
    pass

class FilePath(str):
    pass

class Model:

    @staticmethod
    def _cursor() -> sqlite3.Cursor:
        (conn): sqlite3.Connection = g.sql_conn
        (cur): sqlite3.Cursor = conn.cursor()
        return cur

class _Library(Model):
    id: Optional[LibraryId]
    location: str
    name: str
    parent_id: LibraryId
    fields: dict
    format: str
    TABLE = '_Library'

    def __init__(self, id: Optional[LibraryId], location: str, name: str, parent_id: LibraryId, fields: dict, format: str):
        self.id = id
        self.location = location
        self.name = name
        self.parent_id = parent_id
        self.fields = fields
        self.format = format

    @staticmethod
    def create_table():
        cur = _Library._cursor()
        cur.execute('CREATE TABLE IF NOT EXISTS _Library (id INTEGER PRIMARY KEY ASC, location TEXT, name TEXT, parent_id INTEGER, fields TEXT, format TEXT)')

    @classmethod
    def get(cls, id: LibraryId) -> '_Library':
        cur = cls._cursor()
        cur.execute('SELECT id, location, name, parent_id, fields, format FROM _Library WHERE id = ?', (id,))
        (id, location, name, parent_id, fields_txt, format) = cur.fetchone()
        fields = json.loads(fields_txt)
        return cls(id, location, name, parent_id, fields, format)

    @classmethod
    def new(cls, location: str, name: str, parent_id: LibraryId, fields: dict, format: str) -> '_Library':
        return cls(None, location, name, parent_id, fields, format)

    def save(self):
        cur = self._cursor()
        fields_txt = json.dumps(self.fields)
        if self.id is None:
            cur.execute('INSERT INTO _Library (location, name, parent_id, fields, format) VALUES (?, ?, ?, ?, ?)', (self.location, self.name, self.parent_id, fields_txt, self.format))
            cur.execute('SELECT last_insert_rowid()')
            self.id = cur.fetchone()[0]
        else:
            cur.execute('UPDATE _Library SET location = ?, name = ?, parent_id = ?, fields = ?, format = ? WHERE id = ?', (self.location, self.name, self.parent_id, fields_txt, self.format, self.id))

    @classmethod
    def list(cls, location: Optional[str]=None, name: Optional[str]=None, parent_id: Optional[LibraryId]=None, format: Optional[str]=None) -> ['_Library']:
        params = {'location': location, 'name': name, 'parent_id': parent_id, 'format': format}
        query_terms = []
        query_params = []
        for (name, term) in params.items():
            if term is not None:
                query_terms.append(f'{name} = ?')
                query_params.append(term)
        if query_terms:
            query = ' AND '.join(query_terms)
        else:
            query = '1'
        list_stmt = f'SELECT id, location, name, parent_id, fields, format FROM _Library WHERE {query}'
        cur = cls._cursor()
        cur.execute(list_stmt, query_params)
        results = []
        for row in cur.fetchall():
            (id, location, name, parent_id, fields_txt, format) = row
            fields = json.loads(fields_txt)
            results.append(cls(id, location, name, parent_id, fields, format))
        return results

    def update(self, location: str=None, name: str=None, parent_id: LibraryId=None, fields: dict=None, format: str=None) -> None:
        if location is not None:
            self.location = location
        if name is not None:
            self.name = name
        if parent_id is not None:
            self.parent_id = parent_id
        if fields is not None:
            self.fields = fields
        if format is not None:
            self.format = format

    def to_dict(self) -> dict:
        return {'id': self.id, 'location': self.location, 'name': self.name, 'parent_id': self.parent_id, 'fields': self.fields, 'format': self.format}

    @classmethod
    def from_dict(cls, d: dict) -> '_Library':
        return cls(id=d['id'], location=d['location'], name=d['name'], parent_id=d['parent_id'], fields=d['fields'], format=d['format'])

class _Record(Model):
    id: Optional[RecordId]
    parent_id: LibraryId
    attributes: dict
    referrent: FilePath
    TABLE = '_Record'

    def __init__(self, id: Optional[RecordId], parent_id: LibraryId, attributes: dict, referrent: FilePath):
        self.id = id
        self.parent_id = parent_id
        self.attributes = attributes
        self.referrent = referrent

    @staticmethod
    def create_table():
        cur = _Record._cursor()
        cur.execute('CREATE TABLE IF NOT EXISTS _Record (id INTEGER PRIMARY KEY ASC, parent_id INTEGER, attributes TEXT, referrent TEXT)')

    @classmethod
    def get(cls, id: RecordId) -> '_Record':
        cur = cls._cursor()
        cur.execute('SELECT id, parent_id, attributes, referrent FROM _Record WHERE id = ?', (id,))
        (id, parent_id, attributes_txt, referrent) = cur.fetchone()
        attributes = json.loads(attributes_txt)
        return cls(id, parent_id, attributes, referrent)

    @classmethod
    def new(cls, parent_id: LibraryId, attributes: dict, referrent: FilePath) -> '_Record':
        return cls(None, parent_id, attributes, referrent)

    def save(self):
        cur = self._cursor()
        attributes_txt = json.dumps(self.attributes)
        if self.id is None:
            cur.execute('INSERT INTO _Record (parent_id, attributes, referrent) VALUES (?, ?, ?)', (self.parent_id, attributes_txt, self.referrent))
            cur.execute('SELECT last_insert_rowid()')
            self.id = cur.fetchone()[0]
        else:
            cur.execute('UPDATE _Record SET parent_id = ?, attributes = ?, referrent = ? WHERE id = ?', (self.parent_id, attributes_txt, self.referrent, self.id))

    @classmethod
    def list(cls, parent_id: Optional[LibraryId]=None, referrent: Optional[FilePath]=None) -> ['_Record']:
        params = {'parent_id': parent_id, 'referrent': referrent}
        query_terms = []
        query_params = []
        for (name, term) in params.items():
            if term is not None:
                query_terms.append(f'{name} = ?')
                query_params.append(term)
        if query_terms:
            query = ' AND '.join(query_terms)
        else:
            query = '1'
        list_stmt = f'SELECT id, parent_id, attributes, referrent FROM _Record WHERE {query}'
        cur = cls._cursor()
        cur.execute(list_stmt, query_params)
        results = []
        for row in cur.fetchall():
            (id, parent_id, attributes_txt, referrent) = row
            attributes = json.loads(attributes_txt)
            results.append(cls(id, parent_id, attributes, referrent))
        return results

    def update(self, parent_id: LibraryId=None, attributes: dict=None, referrent: FilePath=None) -> None:
        if parent_id is not None:
            self.parent_id = parent_id
        if attributes is not None:
            self.attributes = attributes
        if referrent is not None:
            self.referrent = referrent

    def to_dict(self) -> dict:
        return {'id': self.id, 'parent_id': self.parent_id, 'attributes': self.attributes, 'referrent': self.referrent}

    @classmethod
    def from_dict(cls, d: dict) -> '_Record':
        return cls(id=d['id'], parent_id=d['parent_id'], attributes=d['attributes'], referrent=d['referrent'])
