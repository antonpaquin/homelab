import pulumi
import pulumi_kubernetes as k8s


class CalibreWebInstallation(pulumi.ComponentResource):
    persistent_volume_claim: k8s.core.v1.PersistentVolumeClaim
    deploy: k8s.apps.v1.Deployment
    service: k8s.core.v1.Service
    secret: k8s.core.v1.Secret

    def __init__(
        self,
        resource_name: str,
        name: str,
        calibre_pvc: k8s.core.v1.PersistentVolumeClaim,
        password: str,
        namespace: str | None = None,
        node_port: int | None = None,
        opts: pulumi.ResourceOptions | None = None,
    ):
        super().__init__('anton:app:CalibreWebInstallation', resource_name, None, opts)

        # OK so calibre is kooky
        # calibre-the-pod uses some kind of vnc crap to expose an xorg-like calibre desktop app
        # and then calibre-web attaches to the DB
        # I'm gonna use /books on calibre as a source of truth, but it's not ingested calibre DB
        # then calibre-web only gets the ingested DB via shared pvc

        if namespace is None:
            namespace = 'default'

        _labels = {'app': 'calibre-web'}

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

        self.secret = k8s.core.v1.Secret(
            resource_name=f'{resource_name}:secret',
            metadata=k8s.meta.v1.ObjectMetaArgs(
                name=name,
                namespace=namespace,
            ),
            string_data={
                'PASSWORD': password,
            },
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
                                env_from=[
                                    k8s.core.v1.EnvFromSourceArgs(
                                        secret_ref=k8s.core.v1.SecretEnvSourceArgs(
                                            name=self.secret.metadata.name,
                                        ),
                                    ),
                                ],
                                volume_mounts=[
                                    k8s.core.v1.VolumeMountArgs(
                                        name='calibre',
                                        mount_path='/calibre',
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
                                name='calibre',
                                persistent_volume_claim=k8s.core.v1.PersistentVolumeClaimVolumeSourceArgs(
                                    claim_name=calibre_pvc.metadata.name,
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
                depends_on=[self.deploy],
            ),
        )