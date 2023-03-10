class ClusterNode:
    name: str
    ip_address: str

    def __init__(self, name: str, ip_address: str) -> None:
        self.name = name
        self.ip_address = ip_address