import typing
import io


ENDIAN = 'little'
INTSIZE = 8


class SerialField:
    def __init__(self, name: str, typ: type, size: typing.Optional[int] = None):
        self.name = name
        self.typ = typ
        self.size = size


class Serial:
    def write_many(self, fields: [SerialField], buf: io.BytesIO):
        for field in fields:
            x = getattr(self, field.name)
            if field.typ == int:
                self.write_int(x, buf)
            elif field.typ == bool:
                self.write_bool(x, buf)
            elif field.typ == bytes:
                if field.size is None:
                    self.write_dyn_bytes(x, buf)
                else:
                    self.write_bytes(x, buf)
            elif field.typ == str:
                self.write_str(x, buf)
            else:
                x.write(buf)

    @classmethod
    def read_many(cls, fields: [SerialField], buf: io.BytesIO):
        res = {}
        for field in fields:
            if field.typ == int:
                x = cls.read_int(buf)
            elif field.typ == bool:
                x = cls.read_bool(buf)
            elif field.typ == bytes:
                if field.size is None:
                    x = cls.read_dyn_bytes(buf)
                else:
                    x = cls.read_bytes(field.size, buf)
            elif field.typ == str:
                x = cls.read_str(buf)
            else:
                x = field.typ.read(buf)
            res[field.name] = x
        return cls(**res)

    def write(self, buf: io.BytesIO) -> None:
        raise NotImplementedError('stub!')

    @staticmethod
    def read(buf: io.BytesIO) -> 'Serial':
        raise NotImplementedError('stub!')

    @staticmethod
    def write_int(x: int, buf: io.BytesIO) -> None:
        buf.write(x.to_bytes(INTSIZE, ENDIAN))

    @staticmethod
    def read_int(buf: io.BytesIO) -> int:
        return int.from_bytes(buf.read(INTSIZE), ENDIAN)

    @staticmethod
    def write_bool(x: bool, buf: io.BytesIO) -> None:
        xb = b'1' if x else b'0'
        buf.write(xb)

    @staticmethod
    def read_bool(buf: io.BytesIO) -> bool:
        return buf.read(1) == b'1'

    @staticmethod
    def write_dyn_bytes(x: bytes, buf: io.BytesIO) -> None:
        Serial.write_int(len(x), buf)
        Serial.write_bytes(x, buf)

    @staticmethod
    def read_dyn_bytes(buf: io.BytesIO) -> bytes:
        l = Serial.read_int(buf)
        return Serial.read_bytes(l, buf)

    @staticmethod
    def write_bytes(x: bytes, buf: io.BytesIO) -> None:
        buf.write(x)

    @staticmethod
    def read_bytes(l: int, buf: io.BytesIO) -> bytes:
        return buf.read(l)

    @staticmethod
    def write_str(x: str, buf: io.BytesIO) -> None:
        Serial.write_dyn_bytes(x.encode('utf-8'), buf)

    @staticmethod
    def read_str(buf: io.BytesIO) -> str:
        return Serial.read_dyn_bytes(buf).decode('utf-8')
