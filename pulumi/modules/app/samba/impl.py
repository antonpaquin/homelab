import textwrap
from typing import List

import pulumi
import pulumi_kubernetes as k8s


class SambaInstallation(pulumi.ComponentResource):
    deployment: k8s.apps.v1.Deployment
    service: k8s.core.v1.Service

    def __init__(
        self,
        resource_name: str,
        name: str,
        namespace: str,
        nfs_server: str,
        nfs_path: str,
        opts: pulumi.ResourceOptions | None = None
    ) -> None:
        super().__init__('anton:app:Samba', resource_name, None, opts)

        _labels = {'app': name}

        self.secret = k8s.core.v1.Secret(
            resource_name=f'{resource_name}:secret',
            metadata=k8s.meta.v1.ObjectMetaArgs(
                name=name,
                namespace=namespace,
            ),
            string_data={
                'smb.conf': textwrap.dedent(f'''
                    [global]
                    workgroup = WORKGROUP
                    log file = /var/log/samba/log.%m
                    logging = file
                    server role = standalone server

                    [library]
                    path = /library
                    read only = no
                ''').strip(),
            },
            opts=pulumi.ResourceOptions(
                parent=self,
            ),
        )

        self.deployment = k8s.apps.v1.Deployment(
            resource_name=f'{resource_name}:deployment',
            metadata=k8s.meta.v1.ObjectMetaArgs(
                name=name,
                namespace=namespace,
            ),
            spec=k8s.apps.v1.DeploymentSpecArgs(
                replicas=1,
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
                                name="samba",
                                image="dperson/samba",
                                args=[
                                    "-I",
                                    '/config/smb.conf',
                                ],
                                ports=[
                                    k8s.core.v1.ContainerPortArgs(
                                        container_port=139,
                                        name="smb",
                                    ),
                                    k8s.core.v1.ContainerPortArgs(
                                        # why is there both 139 and 445?
                                        # even copilot doesn't know
                                        # :shrug:
                                        container_port=445,
                                        name="smb2",
                                    ),
                                ],
                                volume_mounts=[
                                    k8s.core.v1.VolumeMountArgs(
                                        name="config",
                                        mount_path="/config",
                                    ),
                                    k8s.core.v1.VolumeMountArgs(
                                        name="library",
                                        mount_path="/library",
                                    ),
                                ]
                            ),
                        ],
                        volumes=[
                            k8s.core.v1.VolumeArgs(
                                name="config",
                                secret=k8s.core.v1.SecretVolumeSourceArgs(
                                    secret_name=self.secret.metadata.name,
                                ),
                            ),
                            k8s.core.v1.VolumeArgs(
                                name="library",
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

        # bake-in nodeport, I don't think nginx could handle this even if it were set up
        # (todo: metallb?)
        self.service = k8s.core.v1.Service(
            resource_name=f'{resource_name}:service',
            metadata=k8s.meta.v1.ObjectMetaArgs(
                name=name,
                namespace=namespace,
            ),
            spec=k8s.core.v1.ServiceSpecArgs(
                selector=_labels,
                ports=[
                    k8s.core.v1.ServicePortArgs(
                        port=139,
                        target_port="smb",
                        name="smb",
                        node_port=139,
                    ),
                    k8s.core.v1.ServicePortArgs(
                        port=445,
                        target_port="smb2",
                        name="smb2",
                        node_port=445,
                    ),
                ],
                type='NodePort',
            ),
            opts=pulumi.ResourceOptions(
                parent=self,
                depends_on=[self.deployment],
            ),
        )
