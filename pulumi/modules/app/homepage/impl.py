import dataclasses
from typing import List

import pulumi
import pulumi_kubernetes as k8s
import yaml

from modules.lib.boilerplate import simple_env_vars


class HomepageGroup:
    name: str
    services: List['HomepageApp']
    header: bool

    def __init__(
        self, 
        name: str, 
        services: List['HomepageApp'], 
        header: bool = True
    ) -> None:
        self.name = name
        self.services = services
        self.header = header


class HomepageApp:
    name: str
    url: str
    icon: str
    description: str | None

    def __init__(self, name: str, url: str, icon: str, description: str | None = None) -> None:
        self.name = name
        self.url = url
        self.icon = icon
        self.description = description


class HomepageInstallation(pulumi.ComponentResource):
    deploy: k8s.apps.v1.Deployment
    config_map: k8s.core.v1.ConfigMap

    def __init__(
        self,
        resource_name: str,
        name: str,
        namespace: str,
        nfs_server: str,
        nfs_config_path: str,
        apps: List[HomepageGroup] | None = None,
        node_port: int | None = None,
        opts: pulumi.ResourceOptions | None = None,
    ) -> None:
        super().__init__('anton:app:HomepageInstallation', resource_name, None, opts)

        _labels = {'app': 'homepage'}

        if apps is None:
            apps = []

        layouts = {}
        services = []
        for group in apps:
            group_layout = {}
            group_layout['header'] = group.header
            layouts[group.name] = group_layout

            group_services = []
            for service in group.services:
                svc = {
                    'href': service.url,
                    'icon': service.icon,
                }
                if service.description is not None:
                    svc['description'] = service.description

                group_services.append({service.name: svc})
            services.append({group.name: group_services})

        settings = {
            'title': 'Azumanga Cluster',
            'favicon': '/resources/favicon.ico',
            'background': '/resources/background.png',
            'theme': 'dark',
            'layout': layouts,
            'hideVersion': True,
        }

        self.config_map = k8s.core.v1.ConfigMap(
            resource_name=f'{resource_name}:configmap',
            metadata=k8s.meta.v1.ObjectMetaArgs(
                name=name,
                namespace=namespace,
            ),
            data={
                'bookmarks.yaml': '',
                'custom.css': '',
                'custom.js': '',
                'docker.yaml': '',
                'kubernetes.yaml': '',
                'services.yaml': yaml.dump(services),
                'settings.yaml': yaml.dump(settings),
                'widgets.yaml': '',
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
                                name='homepage',
                                image='ghcr.io/gethomepage/homepage:latest',
                                env=simple_env_vars({
                                    'PUID': '1000',
                                    'PGID': '1000',
                                }),
                                ports=[
                                    k8s.core.v1.ContainerPortArgs(
                                        container_port=3000,
                                        name='http',
                                    ),
                                ],
                                volume_mounts=[
                                    k8s.core.v1.VolumeMountArgs(
                                        name='resources',
                                        mount_path='/app/public/resources',
                                    ),
                                    k8s.core.v1.VolumeMountArgs(
                                        name='config',
                                        mount_path='/app/config',
                                    ),
                                ],
                            ),
                        ],
                        volumes=[
                            k8s.core.v1.VolumeArgs(
                                name='resources',
                                nfs=k8s.core.v1.NFSVolumeSourceArgs(
                                    server=nfs_server,
                                    path=nfs_config_path,
                                ),
                            ),
                            k8s.core.v1.VolumeArgs(
                                name='config',
                                config_map=k8s.core.v1.ConfigMapVolumeSourceArgs(
                                    name=self.config_map.metadata.name,
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
                selector=_labels,
                ports=[http_port],
                type=service_type,
            ),
            opts=pulumi.ResourceOptions(
                parent=self,
                depends_on=[self.deploy],
            ),
        )


