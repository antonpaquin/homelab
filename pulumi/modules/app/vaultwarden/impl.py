import pulumi
import pulumi_kubernetes as k8s

from modules.lib.boilerplate import cluster_local_address

class VaultwardenInstallation(pulumi.ComponentResource):
    persistent_volume_claim: k8s.core.v1.PersistentVolumeClaim
    deploy: k8s.apps.v1.Deployment
    service: k8s.core.v1.Service

    def __init__(
        self,
        resource_name: str,
        name: str,
        nfs_server: str,
        nfs_config_path: str,
        namespace: str | None = None,
        node_port: int | None = None,
        opts: pulumi.ResourceOptions | None = None,
    ):
            super().__init__('anton:app:VaultwardenInstallation', resource_name, None, opts)
    
            if namespace is None:
                namespace = 'default'

            self._service_name = name
            self._service_port = 80
            self._namespace = namespace
    
            _labels = {'app': 'vaultwarden'}

            self.deploy = k8s.apps.v1.Deployment(
                resource_name=f'{resource_name}:deploy',
                metadata=k8s.meta.v1.ObjectMetaArgs(
                    name=name,
                    namespace=namespace,
                ),
                spec=k8s.apps.v1.DeploymentSpecArgs(
                    selector=k8s.meta.v1.LabelSelectorArgs(
                        match_labels=_labels,
                    ),
                    template=k8s.core.v1.PodTemplateSpecArgs(
                        metadata=k8s.meta.v1.ObjectMetaArgs(
                            labels=_labels,
                        ),
                        spec=k8s.core.v1.PodSpecArgs(
                            containers=[
                                k8s.core.v1.ContainerArgs(
                                    name='vaultwarden',
                                    image='vaultwarden/server:1.27.0',
                                    ports=[
                                        k8s.core.v1.ContainerPortArgs(
                                            container_port=80,
                                            name='http',
                                        ),
                                    ],
                                    volume_mounts=[
                                        k8s.core.v1.VolumeMountArgs(
                                            name='data',
                                            mount_path='/data',
                                        ),
                                    ],
                                ),
                            ],
                            volumes=[
                                k8s.core.v1.VolumeArgs(
                                    name='data',
                                    nfs=k8s.core.v1.NFSVolumeSourceArgs(
                                        server=nfs_server,
                                        path=nfs_config_path,
                                    ),
                                ),
                            ],
                        ),
                    ),
                ),
                opts=pulumi.ResourceOptions(
                    parent=self,
                    depends_on=[self.persistent_volume_claim],
                ),
            )

            if node_port is not None:
                http_port = k8s.core.v1.ServicePortArgs(
                    port=self._service_port,
                    target_port='http',
                    name='http',
                    node_port=node_port,
                )
                service_type = 'NodePort'
            else:
                http_port = k8s.core.v1.ServicePortArgs(
                    port=self._service_port,
                    target_port='http',
                    name='http',
                )
                service_type = 'ClusterIP'

            self.service = k8s.core.v1.Service(
                resource_name=f'{resource_name}:service',
                metadata=k8s.meta.v1.ObjectMetaArgs(
                    name=self._service_name,
                    namespace=namespace,
                ),
                spec=k8s.core.v1.ServiceSpecArgs(
                    type=service_type,
                    ports=[http_port],
                    selector=_labels,
                ),
                opts=pulumi.ResourceOptions(
                    parent=self,
                    depends_on=[self.deploy],
                ),
            )

    def cluster_local_address(self) -> str:
        return cluster_local_address(self._service_name, self._namespace)
