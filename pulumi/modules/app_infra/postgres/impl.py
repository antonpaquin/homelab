import pulumi
import pulumi_kubernetes as k8s

from modules.lib.config_types import PostgresConnection
from modules.lib.boilerplate import cluster_local_address

class PostgresInstallation(pulumi.ComponentResource):
    chart: k8s.helm.v3.Chart

    _password: str

    def __init__(
        self, 
        resource_name: str, 
        name: str, 
        namespace: str, 
        password: str, 
        storage_size: str, 
        opts: pulumi.ResourceOptions | None = None
    ) -> None:
        super().__init__('anton:app_infra:PostgresInstallation', resource_name, None, opts)

        self._password = password

        self.chart = k8s.helm.v3.Chart(
            release_name=name,
            config=k8s.helm.v3.ChartOpts(
                chart='postgresql',
                namespace=namespace,
                version='11.6.18',
                fetch_opts=k8s.helm.v3.FetchOpts(
                    repo='https://charts.bitnami.com/bitnami'
                ),
                values={
                    'postgresqlUsername': 'postgres',
                    'postgresqlPassword': password,
                    'postgresqlDatabase': 'postgres',
                    'auth': {
                        'database': '_auth',
                    },
                    'service': {
                        'port': 5432,
                    },
                    'persistence': {
                        'size': storage_size,
                        'storageClass': 'nfs-client',
                    },
                    'metrics': {
                        'enabled': True,
                    },
                    'primary': {
                        'containerSecurityContext': {
                            'enabled': True,
                            'runAsUser': 1000,
                        },
                        'podSecurityContext': {
                            'enabled': True,
                            'fsGroup': 1000,
                        },
                    },
                },
            ),
            opts=pulumi.ResourceOptions(
                parent=self,
            )
        )

    def get_connection(self) -> PostgresConnection:
        return PostgresConnection(
            host=cluster_local_address(name='postgres-postgresql', namespace='default'),
            port=5432,
            user='postgres',
            password=self._password,
        )
