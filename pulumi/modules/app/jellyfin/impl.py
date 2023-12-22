import pulumi
import pulumi_kubernetes as k8s

from modules.lib.boilerplate import simple_env_vars


class JellyfinInstallation(pulumi.ComponentResource):
    def __init__(
        self,
        resource_name: str,
        name: str,
        nfs_server: str,
        nfs_config_path: str,
        nfs_db_path: str,
        nfs_media_path: str,
        namespace: str | None = None,
        node_port: int | None = None,
        opts: pulumi.ResourceOptions | None = None,
    ):
        super().__init__("anton:app:jellyfin", resource_name, None, opts)

        if namespace is None:
            namespace = 'default'

        _labels = {'app': 'jellyfin'}

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
                                name='jellyfin',
                                # hack jellyfin to operate dual nfs/local storage; 
                                # see note in docker/jellyfin/README.md
                                image='antonpaquin/misc:jellyfin',
                                env=simple_env_vars({
                                    'JELLYFIN_DB_TEMPLATE': '/_config/data',
                                    'JELLYFIN_DB_HOST': '/config/data'
                                }),
                                ports=[
                                    k8s.core.v1.ContainerPortArgs(
                                        container_port=8096,
                                        name='web',
                                    ),
                                ],
                                volume_mounts=[
                                    k8s.core.v1.VolumeMountArgs(
                                        name='config',
                                        mount_path='/config',
                                    ),
                                    k8s.core.v1.VolumeMountArgs(
                                        name='config_db',
                                        mount_path='/config/data',
                                    ),
                                    k8s.core.v1.VolumeMountArgs(
                                        name='config_db_template',
                                        mount_path='/_config/data',
                                    ),
                                    k8s.core.v1.VolumeMountArgs(
                                        name='media',
                                        mount_path='/media',
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
                                name='config_db',
                                empty_dir=k8s.core.v1.EmptyDirVolumeSourceArgs(),
                            ),
                            k8s.core.v1.VolumeArgs(
                                name='config_db_template',
                                nfs=k8s.core.v1.NFSVolumeSourceArgs(
                                    server=nfs_server,
                                    path=nfs_db_path,
                                ),
                            ),
                            k8s.core.v1.VolumeArgs(
                                name='media',
                                nfs=k8s.core.v1.NFSVolumeSourceArgs(
                                    server=nfs_server,
                                    path=nfs_media_path,
                                ),
                            ),
                        ],
                    ),
                ),
            ),
            opts=pulumi.ResourceOptions(parent=self),
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
                selector=_labels,
                ports=[http_port],
                type=service_type,
            ),
            opts=pulumi.ResourceOptions(
                parent=self,
                depends_on=[self.deploy],
            ),
        )

