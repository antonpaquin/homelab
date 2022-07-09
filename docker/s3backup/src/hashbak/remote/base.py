import typing


class RemoteStorage:
    def upload_meta(self, name: str, contents: typing.Iterable[bytes]) -> None:
        raise NotImplementedError('stub!')

    def list_meta(self) -> [str]:
        raise NotImplementedError('stub!')

    def get_meta(self, name: str) -> typing.Iterable[bytes]:
        raise NotImplementedError('stub!')

    def file_exists(self, fhash: bytes) -> bool:
        raise NotImplementedError('stub!')

    def upload_file(self, fhash: bytes, contents: typing.Iterable[bytes]) -> None:
        raise NotImplementedError('stub!')

    def request_restore(self, fhash: bytes) -> None:
        raise NotImplementedError('stub!')

    def await_restore(self, fhash: bytes) -> None:
        raise NotImplementedError('stub!')

    def get_restored_file(self, fhash: bytes) -> typing.Iterable[bytes]:
        raise NotImplementedError('stub!')

