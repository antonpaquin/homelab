import json
from typing import List

import pulumi
import pulumi_kubernetes as k8s


class HeimdallApp:
    name: str
    url: str
    image_url: str
    color: str

    def __init__(self, name: str, url: str, image_url: str | None = None, color: str | None = None) -> None:
        if image_url is None:
            image_url = ''
            
        if color is None:
            color = '#161b1f'

        self.name = name
        self.url = url
        self.image_url = image_url
        self.color = color


class HeimdallInstallation(pulumi.ComponentResource):
    persistent_volume_claim: k8s.core.v1.PersistentVolumeClaim
    # config_map: k8s.core.v1.ConfigMap
    deploy: k8s.apps.v1.Deployment
    service: k8s.core.v1.Service

    def __init__(
        self,
        resource_name: str,
        name: str,
        namespace: str,
        # apps: List[HeimdallApp],
        node_port: int | None = None,
        opts: pulumi.ResourceOptions | None = None,
    ):
        super().__init__('anton:app:HeimdallInstallation', resource_name, None, opts)

        # "apps" pre-config list disabled; heimdall upgraded and I don't want to go digging into their internal structures for now
        # maybe if 2.5.6 is stable I can settle on that for a while
        # will take re-implementing the sidecar, but pulumi options might be good to do anyway

        self.persistent_volume_claim = k8s.core.v1.PersistentVolumeClaim(
            resource_name=f'{resource_name}:pvc',
            metadata=k8s.meta.v1.ObjectMetaArgs(
                name=name,
                namespace=namespace,
            ),
            spec=k8s.core.v1.PersistentVolumeClaimSpecArgs(
                access_modes=["ReadWriteOnce"],
                resources=k8s.core.v1.ResourceRequirementsArgs(
                    requests={"storage": "100Mi"},
                ),
                storage_class_name="nfs-client",
            ),
            opts=pulumi.ResourceOptions(
                parent=self,
            ),
        )

        # self.config_map = k8s.core.v1.ConfigMap(
        #     resource_name=f'{resource_name}:configmap',
        #     metadata=k8s.meta.v1.ObjectMetaArgs(
        #         name=name,
        #         namespace=namespace,
        #     ),
        #     data={
        #         "apps.json": json.dumps(
        #             [
        #                 {
        #                     "name": app.name,
        #                     "url": app.url,
        #                     "image_url": app.image_url,
        #                     "color": app.color,
        #                 }
        #                 for app in apps
        #             ]
        #         )
        #     },
        #     opts=pulumi.ResourceOptions(
        #         parent=self,
        #     ),
        # )

        _labels = {'app': 'heimdall'}
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
                                name='main',
                                image='docker.io/linuxserver/heimdall:-2.5.6',
                                env=[
                                    k8s.core.v1.EnvVarArgs(
                                        name='PUID',
                                        value='1000',
                                    ),
                                    k8s.core.v1.EnvVarArgs(
                                        name='PGID',
                                        value='1000',
                                    ),
                                    k8s.core.v1.EnvVarArgs(
                                        name='TZ',
                                        value='US/Pacific',
                                    ),
                                ],
                                ports=[
                                    k8s.core.v1.ContainerPortArgs(
                                        name='http',
                                        container_port=80,
                                    ),
                                ],
                                volume_mounts=[
                                    k8s.core.v1.VolumeMountArgs(
                                        name='config',
                                        mount_path='/config/www',
                                    ),
                                ],
                            ),
                            # k8s.core.v1.ContainerArgs(
                            #     name='sidecar',
                            #     image='docker.io/antonpaquin/misc:heimdall-sidecar',
                            #     image_pull_policy='IfNotPresent',
                            #     env=[
                            #         k8s.core.v1.EnvVarArgs(
                            #             name='HEIMDALL_SIDECAR_CONFIG_PATH',
                            #             value='/config/sidecar',
                            #         ),
                            #     ],
                            #     volume_mounts=[
                            #         k8s.core.v1.VolumeMountArgs(
                            #             name='config',
                            #             mount_path='/config/www',
                            #         ),
                            #         k8s.core.v1.VolumeMountArgs(
                            #             name='sidecar-config',
                            #             mount_path='/config/sidecar',
                            #         ),
                            #     ],
                            # ),
                        ],
                        volumes=[
                            k8s.core.v1.VolumeArgs(
                                name='config',
                                persistent_volume_claim=k8s.core.v1.PersistentVolumeClaimVolumeSourceArgs(
                                    claim_name=self.persistent_volume_claim.metadata.name,
                                ),
                            ),
                            # k8s.core.v1.VolumeArgs(
                            #     name='sidecar-config',
                            #     config_map=k8s.core.v1.ConfigMapVolumeSourceArgs(
                            #         name=self.config_map.metadata.name,
                            #     ),
                            # ),
                        ],
                    ),
                ),
            ),
            opts=pulumi.ResourceOptions(
                parent=self,
                depends_on=[self.persistent_volume_claim],
            ),
        )

        if node_port is not None:
            http_port = k8s.core.v1.ServicePortArgs(
                name='http',
                port=80,
                target_port=80,
                node_port=node_port,
            )
            service_type = 'NodePort'
        else:
            http_port = k8s.core.v1.ServicePortArgs(
                name='http',
                port=80,
                target_port=80,
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
