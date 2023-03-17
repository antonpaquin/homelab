import pulumi
import pulumi_kubernetes as k8s


class OverseerrInstallation(pulumi.ComponentResource):
    persistent_volume_claim: k8s.core.v1.PersistentVolumeClaim
    deploy: k8s.apps.v1.Deployment
    service: k8s.core.v1.Service

    def __init__(
        self,
        resource_name: str,
        name: str,
        namespace: str | None = None,
        node_port: int | None = None,
        opts: pulumi.ResourceOptions | None = None,
    ):

        super().__init__('anton:app:OverseerInstallation', resource_name, None, opts)

        if namespace is None:
            namespace = 'default'

        _labels = {'app': 'overseer'}

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
                                name='overseerr',
                                image='docker.io/linuxserver/overseerr:1.32.5',
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
                                ports=[
                                    k8s.core.v1.ContainerPortArgs(
                                        name='http',
                                        container_port=5055,
                                    ),
                                ],
                                volume_mounts=[
                                    k8s.core.v1.VolumeMountArgs(
                                        name='overseerr-config',
                                        mount_path='/config',
                                    ),
                                ],
                            ),
                        ],
                        volumes=[
                            k8s.core.v1.VolumeArgs(
                                name='overseerr-config',
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
                depends_on=[self.persistent_volume_claim],
            ),
        )

        if node_port is not None:
            http_port = k8s.core.v1.ServicePortArgs(
                name='http',
                port=5055,
                target_port='http',
                node_port=node_port,
            )
            service_type = 'NodePort'
        else:
            http_port = k8s.core.v1.ServicePortArgs(
                name='http',
                port=5055,
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
                selector=_labels,
                ports=[http_port],
            ),
            opts=pulumi.ResourceOptions(
                parent=self,
                depends_on=[self.deploy],
            ),
        )
