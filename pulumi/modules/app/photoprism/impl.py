import pulumi
import pulumi_kubernetes as k8s

from modules.lib.boilerplate import simple_secret, simple_configmap, MysqlInitDB
from modules.lib.config_types import MariaDBConnection, InitDB


class PhotoprismInstallation(pulumi.ComponentResource):
    initdb: MysqlInitDB
    secret: k8s.core.v1.Secret
    configmap: k8s.core.v1.ConfigMap
    statefulset: k8s.apps.v1.StatefulSet
    service: k8s.core.v1.Service

    def __init__(
        self, 
        resource_name: str,
        name: str, 
        namespace: str, 
        password: str, 
        db_connection: MariaDBConnection,
        nfs_server: str,
        nfs_photos_path: str,
        nfs_imports_path: str,
        nfs_exports_path: str,
        nodeport: int,
        opts=None,
    ):
        super().__init__('azumanga:app:photoprism', resource_name, None, opts)

        db_name = "photoprism"
        _internal_originals_path = "/photos/originals"
        _internal_exports_path = "/photos/exports"
        _internal_imports_path = "/photos/imports"

        self.initdb = MysqlInitDB(
            resource_name=f'{resource_name}:initdb',
            name=f'{name}-initdb', 
            namespace=namespace, 
            dbname='photoprism', 
            conn=db_connection, 
            opts=pulumi.ResourceOptions(parent=self)
        )

        self.secret = k8s.core.v1.Secret(
            f'{resource_name}:credentials',
            metadata=k8s.meta.v1.ObjectMetaArgs(
                name=name,
                namespace=namespace,
            ),
            string_data={
                "PHOTOPRISM_ADMIN_PASSWORD": password,
                "PHOTOPRISM_DATABASE_SERVER": db_connection.host,
                "PHOTOPRISM_DATABASE_NAME": db_name,
                "PHOTOPRISM_DATABASE_USER": db_connection.user,
                "Photoprism_DATABASE_PASSWORD": db_connection.password,
            },
            opts=pulumi.ResourceOptions(parent=self)
        )

        self.configmap = k8s.core.v1.ConfigMap(
            f'{resource_name}:config',
            metadata=k8s.meta.v1.ObjectMetaArgs(
                name=name,
                namespace=namespace,
            ),
            data={
                "PHOTOPRISM_DEBUG": "true",
                "PHOTOPRISM_CACHE_PATH": "/cache",
                "PHOTOPRISM_IMPORT_PATH": _internal_imports_path,
                "PHOTOPRISM_EXPORT_PATH": _internal_exports_path,
                "PHOTOPRISM_ORIGINALS_PATH": _internal_originals_path,
                "PHOTOPRISM_DATABASE_DRIVER": "mysql",
                "PHOTOPRISM_HTTP_HOST": "0.0.0.0",
                "PHOTOPRISM_HTTP_PORT": "2342",
            },
            opts=pulumi.ResourceOptions(parent=self)
        )

        labels = {'app': 'photoprism'}
        self.statefulset = k8s.apps.v1.StatefulSet(
            resource_name=f'{resource_name}:statefulset',
            metadata=k8s.meta.v1.ObjectMetaArgs(
                name=name,
                namespace=namespace,
            ),
            spec=k8s.apps.v1.StatefulSetSpecArgs(
                service_name='photoprism',
                replicas=1,
                selector=k8s.meta.v1.LabelSelectorArgs(match_labels=labels),
                template=k8s.core.v1.PodTemplateSpecArgs(
                    metadata=k8s.meta.v1.ObjectMetaArgs(labels=labels),
                    spec=k8s.core.v1.PodSpecArgs(
                        init_containers=[
                            self.initdb.init_container,
                        ],
                        containers=[
                            k8s.core.v1.ContainerArgs(
                                name='photoprism',
                                image='docker.io/photoprism/photoprism:latest',
                                env_from=[
                                    k8s.core.v1.EnvFromSourceArgs(
                                        config_map_ref=k8s.core.v1.ConfigMapEnvSourceArgs(
                                            name=self.configmap.metadata.name,
                                        ),
                                    ),
                                    k8s.core.v1.EnvFromSourceArgs(
                                        secret_ref=k8s.core.v1.SecretEnvSourceArgs(
                                            name=self.secret.metadata.name,
                                            optional=False,
                                        ),
                                    ),
                                ],
                                ports=[
                                    k8s.core.v1.ContainerPortArgs(
                                        name='http',
                                        container_port=2342,
                                    ),
                                ],
                                volume_mounts=[
                                    k8s.core.v1.VolumeMountArgs(
                                        name='nfs-originals',
                                        mount_path=_internal_originals_path,
                                    ),
                                    k8s.core.v1.VolumeMountArgs(
                                        name='nfs-exports',
                                        mount_path=_internal_exports_path,
                                    ),
                                    k8s.core.v1.VolumeMountArgs(
                                        name='nfs-imports',
                                        mount_path=_internal_imports_path,
                                    ),
                                ]   ,
                                readiness_probe=k8s.core.v1.ProbeArgs(
                                    http_get=k8s.core.v1.HTTPGetActionArgs(
                                        path='/api/v1/status',
                                        port='http'
                                    ),
                                ),
                            ),
                        ],
                        volumes=[
                            k8s.core.v1.VolumeArgs(
                                name='nfs-originals',
                                nfs=k8s.core.v1.NFSVolumeSourceArgs(
                                    server=nfs_server,
                                    path=nfs_photos_path,
                                ),
                            ),
                            k8s.core.v1.VolumeArgs(
                                name='nfs-exports',
                                nfs=k8s.core.v1.NFSVolumeSourceArgs(
                                    server=nfs_server,
                                    path=nfs_exports_path,
                                ),
                            ),
                            k8s.core.v1.VolumeArgs(
                                name='nfs-imports',
                                nfs=k8s.core.v1.NFSVolumeSourceArgs(
                                    server=nfs_server,
                                    path=nfs_imports_path,
                                ),
                            ),
                            self.initdb.volume,
                        ]
                    ),
                ),
            ),
            opts=pulumi.ResourceOptions(
                parent=self,
                depends_on=[self.secret, self.configmap, self.initdb],
            )
        )

        self.service = k8s.core.v1.Service(
            resource_name=f'{resource_name}:service',
            metadata=k8s.meta.v1.ObjectMetaArgs(
                name=name,
                namespace=namespace,
            ),
            spec=k8s.core.v1.ServiceSpecArgs(
                selector=labels,
                type='NodePort',
                ports=[
                    k8s.core.v1.ServicePortArgs(
                        name='http',
                        port=80,
                        protocol='TCP',
                        target_port='http',
                        node_port=nodeport,
                    ),
                ]
            ),
            opts=pulumi.ResourceOptions(
                parent=self,
                depends_on=[self.statefulset],
            ),
        )
