import hashlib
import textwrap

import pulumi
import pulumi_kubernetes as k8s

from modules.lib.boilerplate import simple_env_vars


class SabnzbdInstallation(pulumi.ComponentResource):
    configmap: k8s.core.v1.ConfigMap
    deploy: k8s.apps.v1.Deployment
    service: k8s.core.v1.Service

    def __init__(
        self, 
        resource_name: str, 
        name: str,
        nfs_data_path: str, 
        nfs_config_path: str,
        nfs_server: str,
        namespace: str | None = None,
        node_port: int | None = None,
        opts: pulumi.ResourceOptions | None = None
    ) -> None:
        super().__init__('anton:app:sabnzbd', resource_name, None, opts)

        if namespace is None:
            namespace = "default"

        _labels = {'app': 'sabnzbd'}

        incomplete_path = f'{nfs_data_path}/progress'
        complete_path = f'{nfs_data_path}/complete'

        self.deploy = k8s.apps.v1.Deployment(
            resource_name=f'{resource_name}:deploy',
            metadata=k8s.meta.v1.ObjectMetaArgs(
                name=name,
                namespace=namespace,
            ),
            spec=k8s.apps.v1.DeploymentSpecArgs(
                selector=k8s.meta.v1.LabelSelectorArgs(match_labels=_labels),
                template=k8s.core.v1.PodTemplateSpecArgs(
                    metadata=k8s.meta.v1.ObjectMetaArgs(labels=_labels),
                    spec=k8s.core.v1.PodSpecArgs(
                        containers=[
                            k8s.core.v1.ContainerArgs(
                                name="main",
                                image="lscr.io/linuxserver/sabnzbd:4.1.0",
                                env=simple_env_vars({
                                    'PUID': '1000',
                                    'PGID': '1000',
                                    'TZ': 'US/Pacific',
                                }),
                                volume_mounts=[
                                    k8s.core.v1.VolumeMountArgs(mount_path='/downloads', name='complete'),
                                    k8s.core.v1.VolumeMountArgs(mount_path='/incomplete-downloads', name='incomplete'),
                                    k8s.core.v1.VolumeMountArgs(mount_path='/config', name='config'),
                                ]
                            ),
                        ],
                        volumes=[
                            k8s.core.v1.VolumeArgs(name='complete', nfs=k8s.core.v1.NFSVolumeSourceArgs(path=complete_path, server=nfs_server)),
                            k8s.core.v1.VolumeArgs(name='incomplete', nfs=k8s.core.v1.NFSVolumeSourceArgs(path=incomplete_path, server=nfs_server)),
                            k8s.core.v1.VolumeArgs(name='config', nfs=k8s.core.v1.NFSVolumeSourceArgs(path=nfs_config_path, server=nfs_server)),
                        ]
                    )
                ),
            ),
            opts=pulumi.ResourceOptions(
                parent=self,
            ),
        )

        if node_port is not None:
            http_port = k8s.core.v1.ServicePortArgs(name='http', port=80, target_port=8080, node_port=node_port)
            svc_type = 'NodePort'
        else:
            http_port = k8s.core.v1.ServicePortArgs(name='http', port=80, target_port=8080)
            svc_type = 'ClusterIP'

        self.service = k8s.core.v1.Service(
            resource_name=f'{resource_name}:service',
            metadata=k8s.meta.v1.ObjectMetaArgs(
                name='sabnzbd',
                namespace=namespace,
            ),
            spec=k8s.core.v1.ServiceSpecArgs(
                selector=_labels,
                ports=[http_port],
                type=svc_type,
            ),
            opts=pulumi.ResourceOptions(
                parent=self,
                depends_on=[self.deploy],
            ),
        )
