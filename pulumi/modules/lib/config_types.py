class ClusterNode:
    name: str
    ip_address: str

    def __init__(self, name: str, ip_address: str) -> None:
        self.name = name
        self.ip_address = ip_address


class MariaDBConnection:
    host: str
    port: int
    user: str
    password: str

    def __init__(self, host: str, port: int, user: str, password: str) -> None:
        self.host = host
        self.port = port
        self.user = user
        self.password = password