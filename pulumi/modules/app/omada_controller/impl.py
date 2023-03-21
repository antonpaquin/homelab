import pulumi
import pulumi_kubernetes as k8s

class OmadaControllerInstallation(pulumi.ComponentResource):
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
        opts: pulumi.ResourceOptions | None = None
    ) -> None:
        super().__init__('anton:app:OmadaControllerInstallation', resource_name, None, opts)

        if namespace is None:
            namespace = 'default'

        ports = [
            k8s.core.v1.ContainerPortArgs(container_port=8088, name='manage-http'),
            k8s.core.v1.ContainerPortArgs(container_port=8043, name='manage-https'),
            k8s.core.v1.ContainerPortArgs(container_port=8843, name='portal-https'),
            k8s.core.v1.ContainerPortArgs(container_port=27001, name='app-discovery', protocol='udp'),
            k8s.core.v1.ContainerPortArgs(container_port=29810, name='discovery', protocol='udp'),
            k8s.core.v1.ContainerPortArgs(container_port=29811, name='manager-v1'),
            k8s.core.v1.ContainerPortArgs(container_port=29812, name='adopt-v1'),
            k8s.core.v1.ContainerPortArgs(container_port=29813, name='upgrade-v1'),
            k8s.core.v1.ContainerPortArgs(container_port=29814, name='manager-v2'),
        ]

        if node_port:
            http_port = k8s.core.v1.ServicePortArgs(port=8088, target_port='manage-http', name='manage-http', node_port=node_port)
            service_type = 'NodePort'
        else:
            http_port = k8s.core.v1.ServicePortArgs(port=8088, target_port='manage-http', name='manage-http')
            service_type = 'ClusterIP'

        service_ports = [
            http_port,
            *[
                k8s.core.v1.ServicePortArgs(port=port.container_port, target_port=port.name, name=port.name, node_port=port.container_port, protocol=port.protocol)
                for port in ports
                if port.name != 'manage-http'
            ]
        ]

        labels = {'app': 'omada-controller'}
        self.deploy = k8s.apps.v1.Deployment(
            f'{resource_name}:deploy',
            metadata=k8s.meta.v1.ObjectMetaArgs(name=name, namespace=namespace),
            spec=k8s.apps.v1.DeploymentSpecArgs(
                selector=k8s.meta.v1.LabelSelectorArgs(match_labels=labels),
                template=k8s.core.v1.PodTemplateSpecArgs(
                    metadata=k8s.meta.v1.ObjectMetaArgs(labels=labels),
                    spec=k8s.core.v1.PodSpecArgs(
                        containers=[
                            k8s.core.v1.ContainerArgs(
                                name='omada-controller',
                                image='mbentley/omada-controller:5.8',
                                env=[
                                    k8s.core.v1.EnvVarArgs(name='PGID', value='508'),
                                    k8s.core.v1.EnvVarArgs(name='PUID', value='508'),
                                    k8s.core.v1.EnvVarArgs(name='TZ', value='America/Los_Angeles'),
                                    k8s.core.v1.EnvVarArgs(name='SHOW_SERVER_LOGS', value='true'),
                                    k8s.core.v1.EnvVarArgs(name='SHOW_MONGODB_LOGS', value='false'),
                                    k8s.core.v1.EnvVarArgs(name='SSL_CERT_NAME', value='tls.crt'),
                                    k8s.core.v1.EnvVarArgs(name='SSL_KEY_NAME', value='tls.key'),
                                    k8s.core.v1.EnvVarArgs(name='MANAGE_HTTP_PORT', value='8088'),
                                    k8s.core.v1.EnvVarArgs(name='PORTAL_HTTP_PORT', value='8088'),
                                    k8s.core.v1.EnvVarArgs(name='MANAGE_HTTPS_PORT', value='8043'),
                                    k8s.core.v1.EnvVarArgs(name='PORTAL_HTTPS_PORT', value='8843'),
                                    k8s.core.v1.EnvVarArgs(name='PORT_APP_DISCOVERY', value='27001'),
                                    k8s.core.v1.EnvVarArgs(name='PORT_DISCOVERY', value='29810'),
                                    k8s.core.v1.EnvVarArgs(name='PORT_MANAGER_V1', value='29811'),
                                    k8s.core.v1.EnvVarArgs(name='PORT_ADOPT_V1', value='29812'),
                                    k8s.core.v1.EnvVarArgs(name='PORT_UPGRADE_V1', value='29813'),
                                    k8s.core.v1.EnvVarArgs(name='PORT_MANAGER_V2', value='29814'),
                                ],
                                volume_mounts=[
                                    k8s.core.v1.VolumeMountArgs(name='data', mount_path='/opt/tplink/EAPController/data'),
                                    k8s.core.v1.VolumeMountArgs(name='logs', mount_path='/opt/tplink/EAPController/logs'),
                                ],
                            ),
                        ],
                        volumes=[
                            k8s.core.v1.VolumeArgs(name='data', nfs=k8s.core.v1.NFSVolumeSourceArgs(server=nfs_server, path=f'{nfs_path}/data')),
                            k8s.core.v1.VolumeArgs(name='logs', nfs=k8s.core.v1.NFSVolumeSourceArgs(server=nfs_server, path=f'{nfs_path}/logs')),
                        ],
                    ),
                ),
            ),
            opts=pulumi.ResourceOptions(parent=self),
        )

        self.service = k8s.core.v1.Service(
            f'{resource_name}:service',
            metadata=k8s.meta.v1.ObjectMetaArgs(name=name, namespace=namespace),
            spec=k8s.core.v1.ServiceSpecArgs(
                type=service_type,
                ports=service_ports,
                selector=labels,
            ),
            opts=pulumi.ResourceOptions(parent=self, depends_on=[self.deploy]),
        )