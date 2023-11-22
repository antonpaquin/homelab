import pulumi
import pulumi_kubernetes as k8s


class SonarrInstallation(pulumi.ComponentResource):
    deploy: k8s.apps.v1.Deployment
    service: k8s.core.v1.Service

    def __init__(
        self,
        resource_name: str,
        name: str,
        nfs_server: str,
        nfs_config_path: str,
        nfs_ingest_path: str,
        nfs_library_path: str,
        namespace: str | None = None,
        node_port: int | None = None,
        opts: pulumi.ResourceOptions | None = None,
    ):
        super().__init__('anton:app:SonarrInstallation', resource_name, None, opts)

        if namespace is None:
            namespace = 'default'

        _labels = {'app': 'sonarr'}

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
                                name='sonarr',
                                image='lscr.io/linuxserver/sonarr:latest',
                                ports=[
                                    k8s.core.v1.ContainerPortArgs(
                                        container_port=8989,
                                        name='web',
                                    ),
                                ],
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
                                        value='America/Los_Angeles',
                                    ),
                                ],
                                volume_mounts=[
                                    k8s.core.v1.VolumeMountArgs(
                                        name='config',
                                        mount_path='/config',
                                    ),
                                    k8s.core.v1.VolumeMountArgs(
                                        name='ingest',
                                        mount_path='/downloads',
                                    ),
                                    k8s.core.v1.VolumeMountArgs(
                                        name='library',
                                        mount_path='/tv',
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
                                name='ingest',
                                nfs=k8s.core.v1.NFSVolumeSourceArgs(
                                    server=nfs_server,
                                    path=nfs_ingest_path,
                                ),
                            ),
                            k8s.core.v1.VolumeArgs(
                                name='library',
                                nfs=k8s.core.v1.NFSVolumeSourceArgs(
                                    server=nfs_server,
                                    path=nfs_library_path,
                                ),
                            ),
                        ]
                    ),
                )
            ),
            opts=opts,
        )

        if node_port is not None:
            http_port = k8s.core.v1.ServicePortArgs(
                name='http',
                port=80,
                target_port='web',
                node_port=node_port,
            )
            service_type = 'NodePort'
        else:
            http_port = k8s.core.v1.ServicePortArgs(
                name='http',
                port=80,
                target_port='web',
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
