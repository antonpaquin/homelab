import datetime
import io
import logging
import os
import typing

import hashbak.fmeta
import hashbak.remote
import hashbak.stream


logger = logging.getLogger(__name__)


def backup(root: str, hash_salt: bytes, storage: hashbak.remote.RemoteStorage):
    name = datetime.datetime.now().strftime('%Y-%m-%d-%H-%M')

    def iter_files() -> typing.Iterable[hashbak.fmeta.FMeta]:
        for path, fdirs, files in os.walk(root):
            for fdir in fdirs:
                fpath = os.path.join(path, fdir)
                yield hashbak.fmeta.FMeta.from_file(fpath, hash_salt, root)
            for file in files:
                fpath = os.path.join(path, file)
                meta = hashbak.fmeta.FMeta.from_file(fpath, hash_salt, root)
                yield meta
                if storage.file_exists(meta.fhash):
                    logger.info(f'File {meta.fname} exists at {meta.fhash.hex()}')
                else:
                    logger.info(f'File {meta.fname}: backing up to {meta.fhash.hex()}')
                    storage.upload_file(meta.fhash, hashbak.stream.file(fpath))

    def serialize_meta():
        for meta in iter_files():
            buf = io.BytesIO()
            meta.write(buf)
            buf.seek(0)
            yield buf.read()

    storage.upload_meta(name, serialize_meta())


def pre_restore(name: str, root: str, hash_salt: bytes, storage: hashbak.remote.RemoteStorage):
    logger.info(f'Beginning un-archive from snapshot {name}')
    metas = hashbak.fmeta.iter_meta(storage.get_meta(name))
    hashes = []
    for meta in metas:
        if not meta.test(root, hash_salt):
            logger.info(f'Attempting to un-archive {meta.fhash.hex()} ({meta.fname})')
            storage.request_restore(meta.fhash)
            hashes.append(meta.fhash)

    for fhash in hashes:
        storage.await_restore(fhash)

    logger.info('Un-archiving complete')


def restore(name: str, root: str, hash_salt: bytes, storage: hashbak.remote.RemoteStorage):
    logger.info(f'Beginning restore from snapshot {name}')
    metas = hashbak.fmeta.iter_meta(storage.get_meta(name))
    for meta in metas:
        logger.info(f'Restoring file {meta.fname}')
        meta.to_file(hash_salt, lambda: storage.get_restored_file(meta.fhash), root)


def full_restore(name: str, root: str, hash_salt: bytes, storage: hashbak.remote.RemoteStorage):
    pre_restore(name, root, hash_salt, storage)
    restore(name, root, hash_salt, storage)
