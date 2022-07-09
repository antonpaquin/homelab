import dataclasses
import enum
import functools
import hashlib
import io
import os
import typing

import hashbak.serial
import hashbak.stream


@functools.lru_cache()
def file_hash(fname: str, salt: bytes) -> bytes:
    """
    Bad: hash the file itself
        Then hash exposes... the file hash, which might get matched against a DB of known files
    Ideal: hash the encrypted contents
        But that's slow
    Practical: hash the unencrypted contents, plus a secret "salt"
    """
    acc = hashlib.sha256()
    acc.update(salt)
    with open(fname, 'rb') as in_f:
        while page := in_f.read(hashbak.stream.PAGE_SIZE):
            acc.update(page)
    return acc.digest()


class FileType(hashbak.serial.Serial, enum.Enum):
    directory = enum.auto()
    file = enum.auto()
    link = enum.auto()

    @staticmethod
    def _byte_code():
        return {
            FileType.directory: b'd',
            FileType.file: b'f',
            FileType.link: b'l',
        }

    def write(self, buf: io.BytesIO):
        self.write_bytes(self._byte_code()[self], buf)

    @staticmethod
    def read(buf: io.BytesIO):
        rev_code = {v: k for k, v in FileType._byte_code().items()}
        key = FileType.read_bytes(1, buf)
        return rev_code[key]

    @staticmethod
    def from_file(fname: str):
        if os.path.islink(fname):
            return FileType.link
        elif os.path.isdir(fname):
            return FileType.directory
        else:
            return FileType.file


@dataclasses.dataclass
class FMeta(hashbak.serial.Serial):
    fname: str
    ftype: FileType
    fhash: bytes
    ino: int
    uid: int
    gid: int
    mode: int
    # yeah, let's ignore attrs, they're dumb anyway

    _fields = [
        hashbak.serial.SerialField('fname', str),
        hashbak.serial.SerialField('ftype', FileType),
        hashbak.serial.SerialField('fhash', bytes),
        hashbak.serial.SerialField('ino', int),
        hashbak.serial.SerialField('uid', int),
        hashbak.serial.SerialField('gid', int),
        hashbak.serial.SerialField('mode', int),
    ]

    def write(self, buf: io.BytesIO):
        self.write_many(FMeta._fields, buf)

    @staticmethod
    def read(buf: io.BytesIO):
        return FMeta.read_many(FMeta._fields, buf)

    @staticmethod
    def from_file(fpath: str, hash_salt: bytes, root: str = ''):
        fname = os.path.abspath(fpath).removeprefix(root)
        ftype = FileType.from_file(fpath)
        if ftype == FileType.file:
            fhash = file_hash(fpath, hash_salt)
        elif ftype == FileType.link:
            fhash = os.readlink(fpath).removeprefix(root).encode('utf-8')
        else:
            fhash = b''
        stat = os.stat(fpath)

        return FMeta(
            fname=fname,
            fhash=fhash,
            ftype=ftype,
            ino=stat.st_ino,
            uid=stat.st_uid,
            gid=stat.st_gid,
            mode=stat.st_mode,
        )

    def to_file(self, hash_salt: bytes, get_contents: typing.Callable[[], typing.Iterable[bytes]] = lambda: b'', root: str = ''):
        fpath = root + self.fname

        if self.ftype == FileType.file:
            if os.path.isfile(fpath):
                fhash = file_hash(fpath, hash_salt)
            else:
                fhash = b''
            if fhash != self.fhash:
                contents = get_contents()
                with open(fpath, 'wb') as out_f:
                    for page in contents:
                        out_f.write(page)
        elif self.ftype == FileType.directory:
            os.makedirs(fpath, exist_ok=True)
        elif self.ftype == FileType.link:
            tgt = self.fhash.decode('utf-8')
            os.symlink(tgt, fpath)

        else:
            raise NotImplementedError('!')

        os.chown(fpath, self.uid, self.gid)
        os.chmod(fpath, self.mode)

    def test(self, root: str, hash_salt: bytes) -> bool:
        if self.ftype != FileType.file:
            return True
        fpath = root + self.fname
        if os.path.isfile(fpath):
            fhash = file_hash(fpath, hash_salt)
        else:
            fhash = b''
        return fhash == self.fhash


def iter_meta(byt: typing.Iterable[bytes]) -> typing.Iterable[FMeta]:
    itr = hashbak.stream.IterIO(byt)
    while itr.more:
        yield FMeta.read(itr)
