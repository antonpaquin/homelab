import textwrap
from typing import Dict, List

import pulumi_kubernetes as k8s

from .config_types import MariaDBConnection, InitDB


def simple_pvc(name: str, namespace: str, storage_request: str, storage_class: str) -> k8s.core.v1.PersistentVolumeClaim:
    return k8s.core.v1.PersistentVolumeClaim(
        resource_name=f'kubernetes-persistentvolumeclaim-{namespace}-{name}',
        metadata=k8s.meta.v1.ObjectMetaArgs(
            name=name,
            namespace=namespace,
        ),
        spec=k8s.core.v1.PersistentVolumeClaimSpecArgs(
            access_modes=["ReadWriteOnce"],
            resources=k8s.core.v1.ResourceRequirementsArgs(
                requests={
                    'storage': storage_request,
                },
            ),
            storage_class_name=storage_class,
        ),
    )

def simple_configmap(name: str, namespace: str, contents: Dict[str, str]) -> k8s.core.v1.ConfigMap:
    return k8s.core.v1.ConfigMap(
        resource_name=f'kubernetes-configmap-{namespace}-{name}',
        metadata=k8s.meta.v1.ObjectMetaArgs(
            name=name,
            namespace=namespace,
        ),
        data=contents
    )

def simple_secret(name: str, namespace: str, contents: Dict[str, str]) -> k8s.core.v1.Secret:
    return k8s.core.v1.Secret(
        resource_name=f'kubernetes-secret-{namespace}-{name}',
        metadata=k8s.meta.v1.ObjectMetaArgs(
            name=name,
            namespace=namespace,
        ),
        string_data=contents
    )

def simple_env_vars(data: Dict[str, str]) -> List[k8s.core.v1.EnvVarArgs]:
    res = []
    for k, v in data.items():
        res.append(k8s.core.v1.EnvVarArgs(name=k, value=v))
    return res


def pvc_volume(name: str, pvc: k8s.core.v1.PersistentVolumeClaim) -> k8s.core.v1.VolumeArgs:
    return k8s.core.v1.VolumeArgs(
        name=name,
        persistent_volume_claim=k8s.core.v1.PersistentVolumeClaimVolumeSourceArgs(
            claim_name=pvc.metadata['name'],
        )
    )

def config_map_volume(name: str, cm: k8s.core.v1.ConfigMap) -> k8s.core.v1.VolumeArgs:
    return k8s.core.v1.VolumeArgs(
        name=name,
        config_map=k8s.core.v1.ConfigMapVolumeSourceArgs(
            name=cm.metadata['name'],
        ),
    )


def cluster_local_address(name: str, namespace: str) -> str:
    return f'{name}.{namespace}.svc.cluster.local'


def service_cluster_local_address(service: k8s.core.v1.Service) -> str:
    return cluster_local_address(service.metadata['name'], service.metadata['namespace'])


def mysql_initdb(dbname: str, namespace: str, conn: MariaDBConnection) -> InitDB:
    secret = simple_secret(f'{dbname}-initdb-credentials', namespace, {
        'DB_USER': conn.user,
        'DB_PASSWORD': conn.password,
        'DB_HOST': conn.host,
        'DB_PORT': str(conn.port),
    })

    cm = simple_configmap(f'{dbname}-initdb', namespace, {
        'entrypoint.sh': textwrap.dedent(f'''
            #! /bin/bash
            
            mysql \\
              --user="$DB_USER" \\
              --password="$DB_PASSWORD" \\
              --host="$DB_HOST" \\
              --port="$DB_PORT" \\
              < /initdb/init.sql
        '''),
        'init.sql': textwrap.dedent(f'''
            CREATE DATABASE IF NOT EXISTS {dbname};
        ''')
    })

    init_container = k8s.core.v1.ContainerArgs(
        name='initdb',
        image='docker.io/bitnami/mariadb:10.5.11-debian-10-r0',
        command=['/initdb/entrypoint.sh'],
        env_from=[
            k8s.core.v1.EnvFromSourceArgs(
                secret_ref=k8s.core.v1.SecretEnvSourceArgs(
                    name=secret.metadata['name'],
                    optional=False,
                ),
            ),
        ],
        volume_mounts=[
            k8s.core.v1.VolumeMountArgs(
                name='initdb',
                mount_path='/initdb',
            ),
        ],
    )

    volume = k8s.core.v1.VolumeArgs(
        name='initdb',
        config_map=k8s.core.v1.ConfigMapVolumeSourceArgs(
            name=cm.metadata['name'],
            default_mode=0o777,
        ),
    )

    return InitDB(
        secret=secret,
        config_map=cm,
        init_container=init_container,
        volume=volume,
    )
