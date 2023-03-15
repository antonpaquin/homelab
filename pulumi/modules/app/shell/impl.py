import textwrap

import pulumi_kubernetes as k8s

from modules.lib.boilerplate import simple_pvc, simple_configmap

from .head import ShellInstallation


def create_shell(
    nfs_server: str,
    nfs_path: str,
    namespace: str | None = None,
) -> ShellInstallation:
    if namespace is None:
        namespace = 'default'

    cm = simple_configmap('shell', namespace, {
        'entrypoint.sh': textwrap.dedent('''
            #! /bin/bash
            
            useradd ubuntu
            tail -f /dev/null
        ''').strip(),
    })

    pvc = simple_pvc('shell', namespace, '10Gi', 'nfs-client')
     
    deploy = k8s.apps.v1.Deployment(
        f'kubernetes-deployment-{namespace}-shell',
        metadata=k8s.meta.v1.ObjectMetaArgs(
            name='shell',
            namespace=namespace,
        ),
        spec=k8s.apps.v1.DeploymentSpecArgs(
            selector=k8s.meta.v1.LabelSelectorArgs(
                match_labels={
                    'app': 'shell',
                },
            ),
            template=k8s.core.v1.PodTemplateSpecArgs(
                metadata=k8s.meta.v1.ObjectMetaArgs(
                    labels={
                        'app': 'shell',
                    },
                ),
                spec=k8s.core.v1.PodSpecArgs(
                    containers=[
                        k8s.core.v1.ContainerArgs(
                            name='main',
                            image='docker.io/antonpaquin/shell:latest',
                            image_pull_policy='Always',
                            command=['/docker/entrypoint.sh'],
                            volume_mounts=[
                                k8s.core.v1.VolumeMountArgs(
                                    name='storage',
                                    mount_path='/storage',
                                ),
                                k8s.core.v1.VolumeMountArgs(
                                    name='shell',
                                    mount_path='/home/ubuntu',
                                ),
                                k8s.core.v1.VolumeMountArgs(
                                    name='config',
                                    mount_path='/docker',
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
                            name='storage',
                            nfs=k8s.core.v1.NFSVolumeSourceArgs(
                                server=nfs_server,
                                path=nfs_path,
                            ),
                        ),
                        k8s.core.v1.VolumeArgs(
                            name='shell',
                            persistent_volume_claim=k8s.core.v1.PersistentVolumeClaimVolumeSourceArgs(
                                claim_name=pvc.metadata['name'],
                            ),
                        ),
                        k8s.core.v1.VolumeArgs(
                            name='config',
                            config_map=k8s.core.v1.ConfigMapVolumeSourceArgs(
                                name=cm.metadata['name'],
                                default_mode=0o755,
                            ),
                        ),
                    ],
                ),
            ),
        ),
    )

    svc = k8s.core.v1.Service(
        f'kubernetes-service-{namespace}-shell',
        metadata=k8s.meta.v1.ObjectMetaArgs(
            name='shell',
            namespace=namespace,
        ),
        spec=k8s.core.v1.ServiceSpecArgs(
            selector={
                'app': 'shell',
            },
            ports=[
                k8s.core.v1.ServicePortArgs(
                    port=8000,
                ),
            ],
        ),
    )

    return ShellInstallation(
        deployment=deploy,
        service=svc,
        configmap=cm,
        persistent_volume_claim=pvc,
    )