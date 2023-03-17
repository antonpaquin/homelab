import pulumi
import pulumi_kubernetes as k8s


class CalibreInstallation(pulumi.ComponentResource):
    persistent_volume_claim: k8s.core.v1.PersistentVolumeClaim
    deploy: k8s.apps.v1.Deployment
    service: k8s.core.v1.Service

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
                access_modes=['ReadWriteMany'],
                resources=k8s.core.v1.ResourceRequirementsArgs(
                    requests={
                        'storage': '5Gi',
                    },
                ),
            ),
            opts=pulumi.ResourceOptions(
                parent=self,
            ),
        )

        self.service = k8s.core.v1.Service(
            resource_name=f'{resource_name}:svc',
            metadata=k8s.meta.v1.ObjectMetaArgs(
                name=name,
                namespace=namespace,
            ),
            spec=k8s.core.v1.ServiceSpecArgs(
                type='ClusterIP',
                selector=_labels,
                ports=[
                    k8s.core.v1.ServicePortArgs(
                        name='http',
                        port=80,
                        target_port=8080,
                    ),
                ],
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
                                image='linuxserver/calibre-web:amd64-version-0.6.19',
                                ports=[
                                    k8s.core.v1.ContainerPortArgs(
                                        container_port=8083,
                                        name='http',
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
                                    k8s.core.v1.EnvVarArgs(
                                        name='DOCKER_MODS',
                                        value='linuxserver/mods:universal-calibre',
                                    ),
                                ],
                                volume_mounts=[
                                    k8s.core.v1.VolumeMountArgs(
                                        name='data',
                                        mount_path='/books',
                                    ),
                                    k8s.core.v1.VolumeMountArgs(
                                        name='config',
                                        mount_path='/config',
                                    ),
                                ],
                            ),
                        ],
                        volumes=[
                            k8s.core.v1.VolumeArgs(
                                name='data',
                                nfs=k8s.core.v1.NFSVolumeSourceArgs(
                                    server=nfs_server,
                                    path=nfs_path,
                                ),
                            ),
                            k8s.core.v1.VolumeArgs(
                                name='config',
                                persistent_volume_claim=k8s.core.v1.PersistentVolumeClaimVolumeSourceArgs(
                                    claim_name=self.persistent_volume_claim.metadata.name,
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
                name="http",
                port=80,
                target_port='http',
                node_port=node_port,
            )
            svc_type = "NodePort"
        else:
            http_port = k8s.core.v1.ServicePortArgs(
                name="http",
                port=80,
                target_port='http',
            )
            svc_type = "ClusterIP"

        self.service = k8s.core.v1.Service(
            resource_name=f'{resource_name}:svc',
            metadata=k8s.meta.v1.ObjectMetaArgs(
                name=name,
                namespace=namespace,
            ),
            spec=k8s.core.v1.ServiceSpecArgs(
                type=svc_type,
                selector=_labels,
                ports=[http_port],
            ),
            opts=pulumi.ResourceOptions(
                parent=self,
            ),
        )