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

        self.persistent_volume = k8s.core.v1.PersistentVolume(
            resource_name=f'{resource_name}:pv',
            metadata=k8s.meta.v1.ObjectMetaArgs(
                name=name,
                namespace=namespace,
            ),
            spec=k8s.core.v1.PersistentVolumeSpecArgs(
                access_modes=['ReadWriteOnce'],
                nfs=k8s.core.v1.NFSVolumeSourceArgs(
                    server=nfs_server,
                    path=nfs_path,
                ),
            ),
            opts=pulumi.ResourceOptions(
                parent=self,
            )
        )

        self.persistent_volume_claim = k8s.core.v1.PersistentVolumeClaim(
            resource_name=f'{resource_name}:pvc',
            metadata=k8s.meta.v1.ObjectMetaArgs(
                name=name,
                namespace=namespace,
            ),
            spec=k8s.core.v1.PersistentVolumeClaimSpecArgs(
                access_modes=['ReadWriteOnce'],
                volume_name=self.persistent_volume.metadata.name,
            ),
            opts=pulumi.ResourceOptions(
                parent=self,
            ),
        )

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
                            'enabled': True,
                            'existingClaim': self.persistent_volume_claim.metadata.name,
                        },
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
