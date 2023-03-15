import textwrap

import pulumi
import pulumi_kubernetes as k8s


class ShellInstallation(pulumi.ComponentResource):
    configmap: k8s.core.v1.ConfigMap
    persistent_volume_claim: k8s.core.v1.PersistentVolumeClaim
    deploy: k8s.apps.v1.Deployment
    service: k8s.core.v1.Service

    def __init__(
        self, 
        resource_name: str,
        name: str, 
        nfs_server: str,
        nfs_path: str,
        namespace: str | None = None,
        opts: pulumi.ResourceOptions | None = None
    ) -> None:
        super().__init__('azumanga:app:ShellInstallation', resource_name, None, opts)

        if namespace is None:
            namespace = 'default'

        self.configmap = k8s.core.v1.ConfigMap(
            resource_name=f'{resource_name}:configmap',
            metadata=k8s.meta.v1.ObjectMetaArgs(
                name=name,
                namespace=namespace,
            ),
            data={
                'entrypoint.sh': textwrap.dedent('''
                    #! /bin/bash
                    
                    useradd ubuntu
                    tail -f /dev/null
                ''').strip(),
            },
            opts=pulumi.ResourceOptions(
                parent=self,
            )
        )

        self.persistent_volume_claim = k8s.core.v1.PersistentVolumeClaim(
            resource_name=f'{resource_name}:pvc',
            metadata=k8s.meta.v1.ObjectMetaArgs(
                name=name,
                namespace=namespace,
            ),
            spec=k8s.core.v1.PersistentVolumeClaimSpecArgs(
                access_modes=["ReadWriteOnce"],
                resources=k8s.core.v1.ResourceRequirementsArgs(
                    requests={
                        'storage': '10Gi',
                    },
                ),
                storage_class_name='nfs-client',
            ),
            opts=pulumi.ResourceOptions(
                parent=self,
            ),
        )

        labels = {'app': 'shell'}
        self.deploy = k8s.apps.v1.Deployment(
            f'{resource_name}:deploy',
            metadata=k8s.meta.v1.ObjectMetaArgs(
                name=name,
                namespace=namespace,
            ),
            spec=k8s.apps.v1.DeploymentSpecArgs(
                selector=k8s.meta.v1.LabelSelectorArgs(match_labels=labels),
                template=k8s.core.v1.PodTemplateSpecArgs(
                    metadata=k8s.meta.v1.ObjectMetaArgs(labels=labels),
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
                                    claim_name=self.persistent_volume_claim.metadata['name'],
                                ),
                            ),
                            k8s.core.v1.VolumeArgs(
                                name='config',
                                config_map=k8s.core.v1.ConfigMapVolumeSourceArgs(
                                    name=self.configmap.metadata['name'],
                                    default_mode=0o755,
                                ),
                            ),
                        ],
                    ),
                ),
            ),
            opts=pulumi.ResourceOptions(
                parent=self,
                depends_on=[self.configmap, self.persistent_volume_claim],
            ),
        )

        self.service = k8s.core.v1.Service(
            f'{resource_name}:service',
            metadata=k8s.meta.v1.ObjectMetaArgs(
                name=name,
                namespace=namespace,
            ),
            spec=k8s.core.v1.ServiceSpecArgs(
                selector=labels,
                ports=[
                    k8s.core.v1.ServicePortArgs(
                        port=8000,
                    ),
                ],
            ),
            opts=pulumi.ResourceOptions(
                parent=self,
                depends_on=[self.deploy],
            )
        )
            