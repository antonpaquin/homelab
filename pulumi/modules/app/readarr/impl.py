import pulumi
import pulumi_kubernetes as k8s


class ReadarrInstallation(pulumi.ComponentResource):
    persistent_volume_claim: k8s.core.v1.PersistentVolumeClaim
    deploy: k8s.apps.v1.Deployment
    service: k8s.core.v1.Service

    def __init__(
        self,
        resource_name: str,
        name: str,
        nfs_server: str,
        nfs_books_path: str,
        nfs_downloads_path: str,
        nfs_config_path: str,
        namespace: str | None = None,
        node_port: int | None = None,
        opts: pulumi.ResourceOptions | None = None,
    ):
        super().__init__('anton:app:ReadarrInstallation', resource_name, None, opts)

        if namespace is None:
            namespace = 'default'

        _labels = {'app': 'readarr'}

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
                                name='readarr',
                                image='linuxserver/readarr:0.1.4-develop',
                                image_pull_policy='IfNotPresent',
                                env=[
                                    k8s.core.v1.EnvVarArgs(
                                        name='PUID',
                                        value='1000',
                                    ),
                                    k8s.core.v1.EnvVarArgs(
                                        name='PGID',
                                        value='1000',
                                    ),
                                    k8s.core.v1.EnvVarArgs(
                                        name='TZ',
                                        value='US/Los_Angeles',
                                    ),
                                ],
                                ports=[
                                    k8s.core.v1.ContainerPortArgs(
                                        name='http',
                                        container_port=8787,
                                    ),
                                ],
                                volume_mounts=[
                                    k8s.core.v1.VolumeMountArgs(
                                        name='config',
                                        mount_path='/config',
                                    ),
                                    k8s.core.v1.VolumeMountArgs(
                                        name='downloads',
                                        mount_path='/downloads',
                                    ),
                                    k8s.core.v1.VolumeMountArgs(
                                        name='books',
                                        mount_path='/books',
                                    ),
                                ],
                            ),
                        ],
                        volumes=[
                            k8s.core.v1.VolumeArgs(
                                name='config',
                                nfs=k8s.core.v1.NFSVolumeSourceArgs(
                                    server=nfs_server,
                                    path=nfs_config_path,
                                ),
                            ),
                            k8s.core.v1.VolumeArgs(
                                name='downloads',
                                nfs=k8s.core.v1.NFSVolumeSourceArgs(
                                    server=nfs_server,
                                    path=nfs_downloads_path,
                                ),
                            ),
                            k8s.core.v1.VolumeArgs(
                                name='books',
                                nfs=k8s.core.v1.NFSVolumeSourceArgs(
                                    server=nfs_server,
                                    path=nfs_books_path,
                                ),
                            ),
                        ],
                    ),
                ),
            ),
            opts=pulumi.ResourceOptions(
                parent=self,
            ),
        )

        if node_port is not None:
            http_port = k8s.core.v1.ServicePortArgs(
                name='http',
                port=80,
                target_port='http',
                node_port=node_port,
            )
            service_type = 'NodePort'
        else:
            http_port = k8s.core.v1.ServicePortArgs(
                name='http',
                port=80,
                target_port='http',
            )
            service_type = 'ClusterIP'

        self.service = k8s.core.v1.Service(
            resource_name=f'{resource_name}:service',
            metadata=k8s.meta.v1.ObjectMetaArgs(
                name=name,
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