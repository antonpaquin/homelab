import pulumi
import pulumi_kubernetes as k8s

from modules.lib.config_types import MariaDBConnection
from modules.lib.boilerplate import cluster_local_address

class MariaDBInstallation(pulumi.ComponentResource):
    chart: k8s.helm.v3.Chart

    _password: str

    def __init__(
        self, 
        resource_name: str, 
        name: str, 
        namespace: str, 
        password: str, 
        nfs_server: str,
        nfs_path: str,
        opts: pulumi.ResourceOptions | None = None
    ) -> None:
        super().__init__('anton:app_infra:MariaDBInstallation', resource_name, None, opts)

        self._password = password

        self.chart = k8s.helm.v3.Chart(
            release_name=name,
            config=k8s.helm.v3.ChartOpts(
                chart='mariadb',
                namespace=namespace,
                version='11.1.0',
                fetch_opts=k8s.helm.v3.FetchOpts(
                    repo='https://charts.bitnami.com/bitnami'
                ),
                values={
                    'auth': {
                        'rootPassword': password,
                    },
                    'primary': {
                        'persistence': {
                            'enabled': False,
                        },
                        'extraVolumes': [
                            {
                                'name': 'data',
                                'nfs': {
                                    'server': nfs_server,
                                    'path': nfs_path,
                                },
                            }
                        ],
                        'extraVolumeMounts': [
                            {
                                'name': 'data',
                                'mountPath': '/bitnami/mariadb',
                            }
                        ],
                    },
                },
            ),
            opts=pulumi.ResourceOptions(
                parent=self,
            )
        )

    def get_connection(self) -> MariaDBConnection:
        return MariaDBConnection(
            host=cluster_local_address(name='mariadb', namespace='default'),
            port=3306,
            user='root',
            password=self._password,
        )
