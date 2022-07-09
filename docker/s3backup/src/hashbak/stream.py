import cryptography.hazmat.primitives.ciphers
import cryptography.hazmat.primitives.ciphers.algorithms
import cryptography.hazmat.primitives.ciphers.modes
import io
import gzip as _gzip
import typing

import hashbak.serial


# AWS multipart has a size minimum of 5MB/chunk (except last chunk)
PAGE_SIZE = 4 * (1024**2)


def file(fname: str) -> typing.Iterable[bytes]:
    with open(fname, 'rb') as in_f:
        while nxt := in_f.read(PAGE_SIZE):
            yield nxt


class IterIO:
    def __init__(self, itr: typing.Iterable[bytes]):
        self.itr = iter(itr)
        self.buf = io.BytesIO()
        self.bufl = 0
        self.more = True

    def read(self, n: typing.Optional[int]) -> bytes:
        res = io.BytesIO()
        remain = n
        while remain > 0 and self.more:
            nxt = self.buf.read(remain)
            remain -= res.write(nxt)
            self.bufl -= len(nxt)
            if self.bufl == 0:
                try:
                    buf_nxt = next(self.itr)
                    self.buf = io.BytesIO(buf_nxt)
                    self.bufl = len(buf_nxt)
                except StopIteration:
                    self.more = False
        res.seek(0)
        return res.read()


def paginate(base: typing.Iterable[bytes], page_size: int = PAGE_SIZE) -> typing.Iterable[bytes]:
    buf = io.BytesIO()
    for nxt in base:
        while nxt:
            pivot = page_size - buf.tell()
            buf.write(nxt[:pivot])
            nxt = nxt[pivot:]
            if buf.tell() == page_size:
                buf.seek(0)
                yield buf.read()
                buf.seek(0)
                buf.truncate()
    buf.seek(0)
    nxt = buf.read()
    if nxt:
        yield nxt


def pad(base: typing.Iterable[bytes], n: int) -> typing.Iterable[bytes]:
    r = 0
    for page in base:
        yield page
        r += len(page)
    tail_length = n - (r % n)
    if tail_length == 0:
        tail_length = n
    tail = b'\x00' * (tail_length - 1) + bytes([tail_length])
    yield tail


def unpad(base: typing.Iterable[bytes]) -> typing.Iterable[bytes]:
    tmp = None
    r = 0
    for page in base:
        if tmp is not None:
            yield tmp
        tmp = page
        r += len(page)
    tail_length = tmp[-1]
    yield tmp[:-tail_length]


def cat(*xss: typing.Iterable[bytes]):
    for xs in xss:
        for x in xs:
            yield x


def apply(xs: typing.Iterable[bytes], fn: typing.Callable[[bytes], bytes]) -> typing.Iterable[bytes]:
    for x in xs:
        yield fn(x)


def call(fn) -> typing.Iterable[bytes]:
    yield fn()


def gzip(xs: typing.Iterable[bytes]) -> typing.Iterable[bytes]:
    for x in paginate(xs):
        res = _gzip.compress(x)
        size = len(res)
        yield size.to_bytes(hashbak.serial.INTSIZE, hashbak.serial.ENDIAN)
        yield res


def ungzip(xs: typing.Iterable[bytes]) -> typing.Iterable[bytes]:
    buf = IterIO(xs)
    while buf.more:
        size = int.from_bytes(buf.read(hashbak.serial.INTSIZE), hashbak.serial.ENDIAN)
        res = buf.read(size)
        yield _gzip.decompress(res)


def split(xs: typing.Iterable[bytes], size: int) -> (bytes, typing.Iterable[bytes]):
    _iter = iter(xs)
    _buf = b''
    while len(_buf) < size:
        nxt = next(_iter)
        _buf += nxt

    return _buf[:size], paginate(cat([_buf[size:]], _iter))


def log(xs: typing.Iterable[bytes], prefix: str = '') -> typing.Iterable[bytes]:
    for x in xs:
        print(prefix, x)
        yield x


def encrypt(base: typing.Iterable[bytes], key: bytes, iv: bytes) -> typing.Iterable[bytes]:
    assert len(iv) == 16
    cipher = cryptography.hazmat.primitives.ciphers.Cipher(
        algorithm=cryptography.hazmat.primitives.ciphers.algorithms.AES(key),
        mode=cryptography.hazmat.primitives.ciphers.modes.CBC(iv),
    )
    enc = cipher.encryptor()

    pd = pad(base, 16)
    enc = cat(apply(pd, enc.update), call(enc.finalize))
    res = cat([iv], enc)
    return paginate(res)


def decrypt(base: typing.Iterable[bytes], key: bytes) -> typing.Iterable[bytes]:
    iv, remain = split(base, 16)

    cipher = cryptography.hazmat.primitives.ciphers.Cipher(
        algorithm=cryptography.hazmat.primitives.ciphers.algorithms.AES(key),
        mode=cryptography.hazmat.primitives.ciphers.modes.CBC(iv),
    )
    dec = cipher.decryptor()

    dec = cat(apply(remain, dec.update), call(dec.finalize))
    upd = unpad(paginate(dec))
    return upd
