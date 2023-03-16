import pulumi
import pulumi_kubernetes as k8s


class PlexInstallation(pulumi.ComponentResource):
    transcode_peristent_volume_claim: k8s.core.v1.PersistentVolumeClaim
    deploy: k8s.apps.v1.Deployment
    service: k8s.core.v1.Service

    def __init__(
        self,
        resource_name: str,
        name: str,
        nfs_server: str,
        nfs_path: str,
        external_ip: str,
        namespace: str | None = None,
        node_port: int | None = None,
        opts: pulumi.ResourceOptions | None = None,
    ):
        super().__init__('anton:app:PlexInstallation', resource_name, None, opts)

        # NB Plex uses a HostPath mount because the index needs locking
        # Is there a better way to achieve that?
        # For now it's stuck on sakaki; possibly do some SAN magic to fix
        # (no, codex, can't use NFS, NFS doesn't support locking)
        # longhorn? Nah, can't mount to the host --> fault tolerance

        self.transcode_peristent_volume_claim = k8s.core.v1.PersistentVolumeClaim(
            resource_name=f'{resource_name}:transcode-pvc',
            metadata=k8s.meta.v1.ObjectMetaArgs(
                name=f'{name}-transcode',
                namespace=namespace,
            ),
            spec=k8s.core.v1.PersistentVolumeClaimSpecArgs(
                access_modes=["ReadWriteOnce"],
                resources=k8s.core.v1.ResourceRequirementsArgs(
                    requests={"storage": "10Gi"},
                ),
                storage_class_name="nfs-client",
            ),
            opts=pulumi.ResourceOptions(
                parent=self,
            ),
        )

        bonus_ports = [
            # plex wants a bunch of crap, let's leave these on the deploy for now and maybe turn on via nodeport later
            #                                                                        '...............' <--- max 15 chars
            k8s.core.v1.ContainerPortArgs(protocol='TCP', container_port=3005,  name='plex-companion'),
            k8s.core.v1.ContainerPortArgs(protocol='TCP', container_port=8324,  name='roku-companion'),
            k8s.core.v1.ContainerPortArgs(protocol='TCP', container_port=32469, name='plex-dlna-tcp'),
            k8s.core.v1.ContainerPortArgs(protocol='UDP', container_port=1900,  name='plex-dlna-udp'),
            k8s.core.v1.ContainerPortArgs(protocol='UDP', container_port=32410, name='gdm-1'),
            k8s.core.v1.ContainerPortArgs(protocol='UDP', container_port=32412, name='gdm-2'),
            k8s.core.v1.ContainerPortArgs(protocol='UDP', container_port=32413, name='gdm-3'),
            k8s.core.v1.ContainerPortArgs(protocol='UDP', container_port=32414, name='gdm-4'),
            k8s.core.v1.ContainerPortArgs(protocol='UDP', container_port=5353,  name='bonjour'),
        ]

        if node_port is not None:
            external_url = f'http://{external_ip}:{node_port}'
        else:
            # ???
            raise NotImplementedError('need to have an external url for whatever expose method')

        _labels = {'app': name}
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
                        node_selector={'kubernetes.io/hostname': 'sakaki'},  # see note re hostpath
                        containers=[
                            k8s.core.v1.ContainerArgs(
                                name='plex',
                                image='plexinc/pms-docker:latest',
                                image_pull_policy='Always',
                                ports=[
                                    k8s.core.v1.ContainerPortArgs(
                                        container_port=32400,
                                        name='http',
                                    ),
                                    *bonus_ports,
                                ],
                                volume_mounts=[
                                    k8s.core.v1.VolumeMountArgs(
                                        name='transcode',
                                        mount_path='/transcode',
                                    ),
                                    k8s.core.v1.VolumeMountArgs(
                                        name='index',
                                        mount_path='/config',
                                    ),
                                    k8s.core.v1.VolumeMountArgs(
                                        name='media',
                                        mount_path='/data',
                                    ),
                                ],
                                env=[
                                    k8s.core.v1.EnvVarArgs(
                                        name='TZ',
                                        value='America/Los_Angeles'   
                                    ),
                                    k8s.core.v1.EnvVarArgs(
                                        name='ADVERTISE_IP',
                                        value=external_url,
                                    ),
                                ],
                            ),
                        ],
                        volumes=[
                            k8s.core.v1.VolumeArgs(
                                name='transcode',
                                persistent_volume_claim=k8s.core.v1.PersistentVolumeClaimVolumeSourceArgs(
                                    claim_name=self.transcode_peristent_volume_claim.metadata.name,
                                ),
                            ),
                            k8s.core.v1.VolumeArgs(
                                name='index',
                                host_path=k8s.core.v1.HostPathVolumeSourceArgs(
                                    path='/data/plex',
                                ),
                            ),
                            k8s.core.v1.VolumeArgs(
                                name='media',
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
                depends_on=[self.transcode_peristent_volume_claim],
            ),
        )

        if node_port is not None:
            service_port = k8s.core.v1.ServicePortArgs(
                port=32400,
                target_port='http',
                node_port=node_port,
                protocol='TCP',
            )
            service_type = 'NodePort'
        else:
            service_port = k8s.core.v1.ServicePortArgs(
                port=32400,
                target_port='http',
                protocol='TCP',
            )
            service_type = 'ClusterIP'

        self.service = k8s.core.v1.Service(
            resource_name=f'{resource_name}:service',
            metadata=k8s.meta.v1.ObjectMetaArgs(
                name=name,
                namespace=namespace,
            ),
            spec=k8s.core.v1.ServiceSpecArgs(
                ports=[service_port],
                type=service_type,
                selector=_labels,
            ),
            opts=pulumi.ResourceOptions(
                parent=self,
                depends_on=[self.deploy],
            ),
        )
