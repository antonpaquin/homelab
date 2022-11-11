import enum
import hashlib
import queue
import threading
import time
import typing

import boto3
import botocore.exceptions

import hashbak.stream

from . import base


def str_hash(contents: str) -> bytes:
    acc = hashlib.sha256()
    acc.update(contents.encode('utf-8'))
    return acc.digest()


class ThreadBufferedS3Download:
    def __init__(self, s3: boto3.client, bucket: str, key: str):
        self.s3 = s3
        self.bucket = bucket
        self.key = key
        self.q = queue.Queue(maxsize=2)
        self.done = False

    def worker(self):
        self.s3.download_fileobj(
            Bucket=self.bucket,
            Key=self.key,
            Fileobj=self,
        )
        self.finish()

    def thread(self):
        t = threading.Thread(target=self.worker, daemon=True)
        t.start()
        # join: calling "finish" is practically a join

    def write(self, byt: bytes) -> int:
        self.q.put(byt)
        return len(byt)

    def finish(self):
        self.done = True
        self.write(b'')

    def deque(self) -> typing.Iterable[bytes]:
        while not self.done:
            item = self.q.get()
            yield item

    def stream(self) -> typing.Iterable[bytes]:
        return hashbak.stream.paginate(self.deque())


class S3Multipart:
    def __init__(self, bucket: str, key: str, storage_class: str, client: boto3.client):
        self.s3 = client
        self.bucket = bucket
        self.key = key
        self.storage_class = storage_class

        self.upload_id = None
        self.idx = 1
        self.parts = []

    def __enter__(self) -> 'S3Multipart':
        response = self.s3.create_multipart_upload(
            Bucket=self.bucket,
            Key=self.key,
            StorageClass=self.storage_class,
        )
        self.upload_id = response['UploadId']
        return self

    def add_chunk(self, data: bytes) -> None:
        resp = self.s3.upload_part(
            Body=data,
            Bucket=self.bucket,
            Key=self.key,
            PartNumber=self.idx,
            UploadId=self.upload_id,
        )
        self.parts.append({
            'ETag': resp['ETag'],
            'PartNumber': self.idx,
        })
        self.idx += 1

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_val is None:
            self.s3.complete_multipart_upload(
                Bucket=self.bucket,
                Key=self.key,
                MultipartUpload={'Parts': self.parts},
                UploadId=self.upload_id,
            )
        else:
            self.s3.abort_multipart_upload(
                Bucket=self.bucket,
                Key=self.key,
                UploadId=self.upload_id,
            )


class RestoreStatus(enum.Enum):
    none = 0
    progress = 1
    complete = 2


class EncryptedS3Storage(base.RemoteStorage):

    def __init__(self, aes_key: bytes, bucket: str):
        self.aes_key = aes_key
        self.bucket = bucket
        self.s3 = boto3.client('s3')

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
        return f'hashbak/snapshots/{name}'

    @staticmethod
    def _file_name(fhash: bytes):
        return f'hashbak/file/{fhash.hex()}'

    @staticmethod
    def _restore_name(fhash: bytes):
        return EncryptedS3Storage._file_name(fhash)

    def upload_meta(self, name: str, contents: typing.Iterable[bytes]) -> None:
        iv = str_hash(name)[:16]
        enc = self._encrypt(contents, self.aes_key, iv)
        key = self._meta_name(name)
        parts = hashbak.stream.paginate(enc, 10*(1024**2))
        with S3Multipart(bucket=self.bucket, key=key, storage_class='STANDARD', client=self.s3) as multipart:
            for part in parts:
                multipart.add_chunk(part)

    def list_meta(self) -> [str]:
        paginator = self.s3.get_paginator('list_objects_v2')
        response_iterator = paginator.paginate(
            Bucket=self.bucket,
            Delimiter='/',
            Prefix=self._meta_name(''),
        )
        res = []
        for entry in response_iterator:
            for x in entry['Contents']:
                res.append(x['Key'])
        return res

    def get_meta(self, name: str) -> typing.Iterable[bytes]:
        key = self._meta_name(name)
        dl = ThreadBufferedS3Download(self.s3, self.bucket, key)
        dl.thread()
        return self._decrypt(dl.stream(), self.aes_key)

    def file_exists(self, fhash: bytes) -> bool:
        try:
            self.s3.head_object(
                Bucket=self.bucket,
                Key=self._file_name(fhash),
            )
            return True
        except botocore.exceptions.ClientError:
            return False

    def upload_file(self, fhash: bytes, contents: typing.Iterable[bytes]) -> None:
        enc = self._encrypt(contents, self.aes_key, fhash[:16])
        # This will break if we go above 100Gi (AWS maxes at 10_000 parts)
        parts = hashbak.stream.paginate(enc, 10*(1024**2))
        with S3Multipart(bucket=self.bucket, key=self._file_name(fhash), storage_class='GLACIER', client=self.s3) as multipart:
            for part in parts:
                multipart.add_chunk(part)

    def _test_restore(self, fhash: bytes) -> RestoreStatus:
        key = self._restore_name(fhash)
        response = self.s3.head_object(
            Bucket=self.bucket,
            Key=key,
        )
        if 'Restore' not in response:
            return RestoreStatus.none
        elif '''ongoing-request="false"''' in response["Restore"]:
            return RestoreStatus.complete
        else:
            return RestoreStatus.progress

    def request_restore(self, fhash: bytes) -> None:
        key = self._restore_name(fhash)
        if self._test_restore(fhash) == RestoreStatus.none:
            response = self.s3.restore_object(
                Bucket=self.bucket,
                Key=key,
                RestoreRequest={
                    'Days': 7,
                    'GlacierJobParameters': {
                        'Tier': 'Bulk',
                    },
                },
            )

    def await_restore(self, fhash: bytes) -> None:
        while True:
            status = self._test_restore(fhash)
            if status == RestoreStatus.complete:
                return
            else:
                assert status == RestoreStatus.progress
                time.sleep(60)

    def get_restored_file(self, fhash: bytes) -> typing.Iterable[bytes]:
        key = self._restore_name(fhash)
        dl = ThreadBufferedS3Download(self.s3, self.bucket, key)
        dl.thread()
        return self._decrypt(dl.stream(), self.aes_key)
