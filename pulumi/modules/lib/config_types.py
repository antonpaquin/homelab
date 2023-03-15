import pulumi
import pulumi_kubernetes as k8s


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


class InitDB:
    secret: k8s.core.v1.Secret
    config_map: k8s.core.v1.ConfigMap
    init_container: k8s.core.v1.ContainerArgs
    volume: k8s.core.v1.VolumeArgs

    def __init__(
        self,
        secret: k8s.core.v1.Secret,
        config_map: k8s.core.v1.ConfigMap,
        init_container: k8s.core.v1.ContainerArgs,
        volume: k8s.core.v1.VolumeArgs
    ) -> None:
        self.secret = secret
        self.config_map = config_map
        self.init_container = init_container
        self.volume = volume
