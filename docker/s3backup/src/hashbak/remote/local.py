import hashlib
import os
import shutil
import time
import typing

import hashbak.stream

from . import base


def str_hash(contents: str) -> bytes:
    acc = hashlib.sha256()
    acc.update(contents.encode('utf-8'))
    return acc.digest()


class EncryptedLocalStorage(base.RemoteStorage):

    def __init__(self, aes_key: bytes):
        self.aes_key = aes_key

    @staticmethod
    def _encrypt(contents: typing.Iterable[bytes], key: bytes, iv: bytes) -> typing.Iterable[bytes]:
        gzs = hashbak.stream.gzip(contents)
        enc = hashbak.stream.encrypt(gzs, key, iv)
        return enc

    @staticmethod
    def _decrypt(contents: typing.Iterable[bytes], key: bytes) -> typing.Iterable[bytes]:
        dec = hashbak.stream.decrypt(contents, key)
        ugz = hashbak.stream.ungzip(dec)
        return hashbak.stream.paginate(ugz)

    @staticmethod
    def _meta_name(name: str):
        return f'/home/anton/tmp/mock_s3/meta/{name}'

    @staticmethod
    def _file_name(fhash: bytes):
        return f'/home/anton/tmp/mock_s3/file/{fhash.hex()}'

    @staticmethod
    def _restore_name(fhash: bytes):
        return f'/home/anton/tmp/mock_s3/restore/{fhash.hex()}'

    def upload_meta(self, name: str, contents: typing.Iterable[bytes]) -> None:
        iv = str_hash(name)[:16]
        enc = self._encrypt(contents, self.aes_key, iv)
        with open(self._meta_name(name), 'wb') as out_f:
            for page in enc:
                out_f.write(page)

    def list_meta(self) -> [str]:
        return os.listdir('/home/anton/tmp/mock_s3/meta')

    def get_meta(self, name: str) -> typing.Iterable[bytes]:
        return self._decrypt(hashbak.stream.file(self._meta_name(name)), self.aes_key)

    def file_exists(self, fhash: bytes) -> bool:
        return os.path.exists(self._file_name(fhash))

    def upload_file(self, fhash: bytes, contents: typing.Iterable[bytes]) -> None:
        enc = self._encrypt(contents, self.aes_key, fhash[:16])
        with open(self._file_name(fhash), 'wb') as out_f:
            for page in enc:
                out_f.write(page)

    def request_restore(self, fhash: bytes) -> None:
        shutil.copy(self._file_name(fhash), self._restore_name(fhash))

    def await_restore(self, fhash: bytes) -> None:
        while not os.path.isfile(self._restore_name(fhash)):
            time.sleep(1)

    def get_restored_file(self, fhash: bytes) -> typing.Iterable[bytes]:
        return self._decrypt(hashbak.stream.file(self._restore_name(fhash)), self.aes_key)
