import pulumi
import pulumi_kubernetes as k8s


class CalibreInstallation(pulumi.ComponentResource):
    deploy: k8s.apps.v1.Deployment
    service: k8s.core.v1.Service
    persistent_volume_claim: k8s.core.v1.PersistentVolumeClaim

    def __init__(
        self,
        resource_name: str,
        name: str,
        nfs_server: str,
        nfs_path: str,
        namespace: str | None = None,
        node_port: int | None = None,
        opts: pulumi.ResourceOptions | None = None,
    ):

        super().__init__('anton:app:CalibreInstallation', resource_name, None, opts)

        if namespace is None:
            namespace = 'default'

        _labels = {'app': 'calibre'}

        self.persistent_volume_claim = k8s.core.v1.PersistentVolumeClaim(
            resource_name=f'{resource_name}:pvc',
            metadata=k8s.meta.v1.ObjectMetaArgs(
                name=name,
                namespace=namespace,
            ),
            spec=k8s.core.v1.PersistentVolumeClaimSpecArgs(
                access_modes=['ReadWriteOnce'],
                resources=k8s.core.v1.ResourceRequirementsArgs(
                    requests={
                        'storage': '20Gi',
                    },
                ),
                storage_class_name='nfs-client',
            ),
            opts=pulumi.ResourceOptions(
                parent=self,
            ),
        )

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
                                name='calibre',
                                image='lscr.io/linuxserver/calibre:6.14.1',
                                ports=[
                                    # linuxserver claims that 8080 is desktop and 8081 is web
                                    # but 8081 just refuses connections
                                    # why?

                                    # the hell it's some kind of vnc thing
                                    # whyyyy

                                    # k8s.core.v1.ContainerPortArgs(
                                    #     container_port=8080,
                                    #     name='desktop',
                                    # ),
                                    k8s.core.v1.ContainerPortArgs(
                                        container_port=8080,
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
                                        name='calibre',
                                        mount_path='/calibre',
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
                                name='calibre',
                                persistent_volume_claim=k8s.core.v1.PersistentVolumeClaimVolumeSourceArgs(
                                    claim_name=self.persistent_volume_claim.metadata.name,
                                ),
                            ),
                            k8s.core.v1.VolumeArgs(
                                name='books',
                                nfs=k8s.core.v1.NFSVolumeSourceArgs(
                                    server=nfs_server,
                                    path=nfs_path,
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
