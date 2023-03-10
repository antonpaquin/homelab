import pulumi_kubernetes as k8s

class MariaDBInstallation:
    chart: k8s.helm.v3.Chart

    port: int
    service_name: str
    namespace: str
    user: str
    password: str

    def __init__(
        self,
        chart: k8s.helm.v3.Chart,
        namespace: str,
        port: int,
        service_name: str,
        user: str,
        password: str
    ) -> None:
        self.chart = chart

        self.namespace = namespace
        self.service_name = service_name
        self.port = port
        self.user = user
        self.password = password
