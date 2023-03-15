import pulumi_kubernetes as k8s

from modules.lib.boilerplate import mysql_initdb, simple_secret, simple_configmap
from modules.lib.config_types import MariaDBConnection

from .head import PhotoprismInstallation


def create_photoprism(
    password: str, 
    namespace: str, 
    db_connection: MariaDBConnection,
    nfs_server: str,
    nfs_photos_path: str,
    nfs_imports_path: str,
    nfs_exports_path: str,
    nodeport: int,
) -> PhotoprismInstallation:

    db_name = "photoprism"
    initdb = mysql_initdb(db_name, namespace, db_connection)

    _internal_originals_path = "/photos/originals"
    _internal_exports_path = "/photos/exports"
    _internal_imports_path = "/photos/imports"


    secret = simple_secret('photoprism', namespace, {
        "PHOTOPRISM_ADMIN_PASSWORD": password,
        "PHOTOPRISM_DATABASE_SERVER": db_connection.host,
        "PHOTOPRISM_DATABASE_NAME": db_name,
        "PHOTOPRISM_DATABASE_USER": db_connection.user,
        "Photoprism_DATABASE_PASSWORD": db_connection.password,
    })

    configmap = simple_configmap('photoprism', namespace, {
        "PHOTOPRISM_DEBUG": "true",
        "PHOTOPRISM_CACHE_PATH": "/cache",
        "PHOTOPRISM_IMPORT_PATH": _internal_imports_path,
        "PHOTOPRISM_EXPORT_PATH": _internal_exports_path,
        "PHOTOPRISM_ORIGINALS_PATH": _internal_originals_path,
        "PHOTOPRISM_DATABASE_DRIVER": "mysql",
        "PHOTOPRISM_HTTP_HOST": "0.0.0.0",
        "PHOTOPRISM_HTTP_PORT": "2342",
    })

    sts = k8s.apps.v1.StatefulSet(
        resource_name=f'kubernetes-statefulset-{namespace}-photoprism',
        metadata=k8s.meta.v1.ObjectMetaArgs(
            name='photoprism',
            namespace=namespace,
        ),
        spec=k8s.apps.v1.StatefulSetSpecArgs(
            service_name='photoprism',
            replicas=1,
            selector=k8s.meta.v1.LabelSelectorArgs(
                match_labels={
                    "app": "photoprism",
                },
            ),
            template=k8s.core.v1.PodTemplateSpecArgs(
                metadata=k8s.meta.v1.ObjectMetaArgs(
                    labels={
                        "app": "photoprism",
                    },
                ),
                spec=k8s.core.v1.PodSpecArgs(
                    init_containers=[
                        initdb.init_container,
                    ],
                    containers=[
                        k8s.core.v1.ContainerArgs(
                            name='photoprism',
                            image='docker.io/photoprism/photoprism:latest',
                            env_from=[
                                k8s.core.v1.EnvFromSourceArgs(
                                    config_map_ref=k8s.core.v1.ConfigMapEnvSourceArgs(
                                        name=configmap.metadata.name,
                                    ),
                                ),
                                k8s.core.v1.EnvFromSourceArgs(
                                    secret_ref=k8s.core.v1.SecretEnvSourceArgs(
                                        name=secret.metadata.name,
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
                                    mount_path=_internal_originals_path,
                                ),
                                k8s.core.v1.VolumeMountArgs(
                                    name='nfs-imports',
                                    mount_path=_internal_originals_path,
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
                        initdb.volume,
                    ]
                ),
            ),
        ),
    )

    service = k8s.core.v1.Service(
        resource_name=f'kubernetes-service-{namespace}-photoprism',
        metadata=k8s.meta.v1.ObjectMetaArgs(
            name='photoprism',
            namespace=namespace,
        ),
        spec=k8s.core.v1.ServiceSpecArgs(
            selector={
                "app": "photoprism",
            },
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
    )

    return PhotoprismInstallation(
        initdb=initdb,
        secret=secret,
        configmap=configmap,
        sts=sts,
        service=service,
    )
