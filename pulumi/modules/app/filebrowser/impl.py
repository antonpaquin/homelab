import textwrap

import pulumi
import pulumi_kubernetes as k8s


class FilebrowserInstallation(pulumi.ComponentResource):
    config_map: k8s.core.v1.ConfigMap
    deployment: k8s.apps.v1.Deployment
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
        super().__init__('anton:app:FilebrowserInstallation', resource_name, None, opts)

        if namespace is None:
            namespace = 'default'

        _internal_port = 7121
        _labels = {'app': 'filebrowser'}

        self.config_map = k8s.core.v1.ConfigMap(
            resource_name=f'{resource_name}:configmap',
            metadata=k8s.meta.v1.ObjectMetaArgs(
                name=name,
                namespace=namespace,
            ),
            data={
                'filebrowser.json': textwrap.dedent('''
                    {
                        "port": ''' + str(_internal_port) + ''',
                        "baseURL": "",
                        "address": "",
                        "log": "stdout",
                        "database": "/tmp/filebrowser.db",
                        "root": "/srv"
                    }
                ''').strip(),
                'entrypoint.sh': textwrap.dedent('''
                    #! /bin/sh
                    
                    set -e
                    
                    # NB: the config json is just CLI params, "config set" is separate
                    # There must be a user, but with method=noauth it's just a dummy
                    
                    /filebrowser -c /etc/filebrowser/filebrowser.json config init
                    /filebrowser -c /etc/filebrowser/filebrowser.json config set --auth.method=noauth
                    /filebrowser -c /etc/filebrowser/filebrowser.json users add nouser nopass
                    /filebrowser -c /etc/filebrowser/filebrowser.json
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
                selector=k8s.meta.v1.LabelSelectorArgs(match_labels=_labels),
                template=k8s.core.v1.PodTemplateSpecArgs(
                    metadata=k8s.meta.v1.ObjectMetaArgs(labels=_labels),
                    spec=k8s.core.v1.PodSpecArgs(
                        containers=[
                            k8s.core.v1.ContainerArgs(
                                name='main',
                                image='docker.io/filebrowser/filebrowser:v2.15.0',
                                command=['/etc/filebrowser/entrypoint.sh'],
                                volume_mounts=[
                                    k8s.core.v1.VolumeMountArgs(
                                        name='library',
                                        mount_path='/srv',
                                    ),
                                    k8s.core.v1.VolumeMountArgs(
                                        name='config',
                                        mount_path='/etc/filebrowser',
                                    ),
                                ],
                                security_context=k8s.core.v1.SecurityContextArgs(
                                    run_as_user=1000,
                                    run_as_group=1000,
                                ),
                            ),
                        ],
                        volumes=[
                            k8s.core.v1.VolumeArgs(
                                name='media',
                                nfs=k8s.core.v1.NFSVolumeSourceArgs(
                                    server=nfs_server,
                                    path=nfs_path,
                                ),
                            ),
                            k8s.core.v1.VolumeArgs(
                                name='config',
                                config_map=k8s.core.v1.ConfigMapVolumeSourceArgs(
                                    name=self.config_map.metadata.name,
                                    items=[
                                        k8s.core.v1.KeyToPathArgs(
                                            key='entrypoint.sh',
                                            path='entrypoint.sh',
                                            mode=0o777,
                                        ),
                                        k8s.core.v1.KeyToPathArgs(
                                            key='filebrowser.json',
                                            path='filebrowser.json',
                                        ),
                                    ],
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

        if node_port is not None:
            http_port = k8s.core.v1.ServicePortArgs(
                name="http",
                port=80,
                target_port=8080,
                node_port=node_port,
            )
            svc_type = "NodePort"
        else:
            http_port = k8s.core.v1.ServicePortArgs(
                name="http",
                port=80,
                target_port=8080,
            )
            svc_type = "ClusterIP"


        self.service = k8s.core.v1.Service(
            resource_name=f'{resource_name}:service',
            metadata=k8s.meta.v1.ObjectMetaArgs(
                name=name,
                namespace=namespace,
            ),
            spec=k8s.core.v1.ServiceSpecArgs(
                selector=_labels,
                ports=[http_port],
                type=svc_type,
            ),
            opts=pulumi.ResourceOptions(
                parent=self,
                depends_on=[self.deployment],
            ),
        )



# resource "kubernetes_service" "filebrowser" {
#   metadata {
#     name = "filebrowser"
#     namespace = local.namespace
#   }
#   spec {
#     selector = {
#       app = "filebrowser"
#     }
#     port {
#       port = 80
#       target_port = local.internal_port
#       name = "http"
#     }
#   }
# }
# 
# module "protected_ingress" {
#   source = "../../../modules/app_infra/authproxy/protected_ingress"
#   host = local.host
#   authproxy_host = var.authproxy_host
#   name = "filebrowser"
#   namespace = local.namespace
#   service_name = kubernetes_service.filebrowser.metadata[0].name
#   service_port = "http"
#   extra_annotations = {
#     "nginx.ingress.kubernetes.io/proxy-send-timeout": 3600
#     "nginx.ingress.kubernetes.io/proxy-read-timeout": 3600
#     "nginx.ingress.kubernetes.io/proxy-body-size": "8192m"
# 
#     # "nginx.ingress.kubernetes.io/configuration-snippet": "client_max_body_size 5tb;"
# 
#   }
#   tls_secret = var.tls_secret
# }
# 
# output "host" {
#   value = local.host
# }
# 
#     '''