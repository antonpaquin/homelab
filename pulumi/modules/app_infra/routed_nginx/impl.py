import textwrap
from typing import List

import pulumi
import pulumi_kubernetes as k8s


class NginxPort:
    name: str
    hostname: str
    service_port: int
    external_port: int

    def __init__(
        self,
        name: str,
        hostname: str,
        service_port: int,
        external_port: int,
    ) -> None:
        self.name = name
        self.hostname = hostname
        self.service_port = service_port
        self.external_port = external_port


class RoutedNginx(pulumi.ComponentResource):
    def __init__(
        self,
        resource_name: str,
        name: str,
        ports: List[NginxPort],
        ssl_crt_data: str,
        ssl_key_data: str,
        namespace: str | None = None,
        opts: pulumi.ResourceOptions | None = None,
    ):
        super().__init__('anton:app:RoutedNginx', resource_name, None, opts)

        if namespace is None:
            namespace = 'default'

        _labels = {'app': 'routed-nginx'}

        server_blocks = []
        for port in ports:
            server_block_tmpl = textwrap.dedent('''
                server {
                    listen SERVICE_PORT ssl;
                    ssl_certificate     /etc/nginx/ssl.crt;
                    ssl_certificate_key /etc/nginx/ssl.key;
                    ssl_protocols       TLSv1 TLSv1.1 TLSv1.2;
                    ssl_ciphers         HIGH:!aNULL:!MD5;
                    location / {
                        proxy_pass http://HOSTNAME:SERVICE_PORT;
                    }
                }
            ''').strip()
            server_block = server_block_tmpl.replace('SERVICE_PORT', str(port.service_port)).replace('HOSTNAME', port.hostname)
            server_blocks.append(server_block)

        server_block_repl = textwrap.indent('\n'.join(server_blocks), ' '*8)

        self.config_map = k8s.core.v1.ConfigMap(
            resource_name=f'{resource_name}:config',
            metadata=k8s.meta.v1.ObjectMetaArgs(
                name=name,
                namespace=namespace,
            ),
            data={
                'nginx.conf': textwrap.dedent('''
                    http {
                        SERVER_BLOCKS
                    }
                ''').strip().replace('SERVER_BLOCKS', server_block_repl),
                'ssl.crt': ssl_crt_data,
                'ssl.key': ssl_key_data,
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
                                name='routed-nginx',
                                image='nginx:1.21.3',
                                ports=[
                                    k8s.core.v1.ContainerPortArgs(
                                        container_port=port.service_port,
                                        name=port.name,
                                    )
                                    for port in ports
                                ],
                                volume_mounts=[
                                    k8s.core.v1.VolumeMountArgs(
                                        name='nginx-config',
                                        mount_path='/etc/nginx',
                                    ),
                                ],
                            ),
                        ],
                        volumes=[
                            k8s.core.v1.VolumeArgs(
                                name='nginx-config',
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
                depends_on=[self.config_map],
            ),
        )

        self.service = k8s.core.v1.Service(
            resource_name=f'{resource_name}:service',
            metadata=k8s.meta.v1.ObjectMetaArgs(
                name=name,
                namespace=namespace,
            ),
            spec=k8s.core.v1.ServiceSpecArgs(
                type='NodePort',
                selector=_labels,
                ports=[
                    k8s.core.v1.ServicePortArgs(
                        port=port.service_port,
                        target_port=port.name,
                        name=port.name,
                        node_port=port.external_port,
                    )
                    for port in ports
                ],
            ),
            opts=pulumi.ResourceOptions(
                parent=self,
                depends_on=[self.deploy],
            ),
        )


        pass