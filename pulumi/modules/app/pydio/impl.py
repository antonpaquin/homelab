import textwrap

import pulumi
import pulumi_kubernetes as k8s

from modules.lib.boilerplate import simple_configmap, MysqlInitDB
from modules.lib.config_types import MariaDBConnection


class PydioInstallation(pulumi.ComponentResource):
    persistent_volume_claim: k8s.core.v1.PersistentVolumeClaim
    initdb: MysqlInitDB
    configmap: k8s.core.v1.ConfigMap
    deploy: k8s.apps.v1.Deployment

    def __init__(
        self, 
        resource_name: str,
        name: str,
        username: str,
        password: str,
        mariaDB: MariaDBConnection,
        node_port: int | None = None, 
        namespace: str | None = None,
        opts: pulumi.ResourceOptions | None = None,
    ) -> None:
        super().__init__('anton:app:pydio', name, None, opts)

        if namespace is None:
            namespace = "default"

        dbname = 'cells'
        labels = {'app': 'pydio'}

        self.persistent_volume_claim = k8s.core.v1.PersistentVolumeClaim(
            f"{resource_name}:pvc",
            metadata=k8s.meta.v1.ObjectMetaArgs(
                name=name,
                namespace=namespace,
                labels=labels,
            ),
            spec=k8s.core.v1.PersistentVolumeClaimSpecArgs(
                access_modes=["ReadWriteOnce"],
                resources=k8s.core.v1.ResourceRequirementsArgs(
                    requests={"storage": "2Gi"},
                ),
                storage_class_name="nfs-client",
            ),
            opts=pulumi.ResourceOptions(
                parent=self,
            ),
        )

        self.initdb = MysqlInitDB(
            resource_name=f"{resource_name}:initdb",
            name=f'{name}-initdb',
            namespace=namespace,
            dbname=dbname,
            conn=mariaDB,
            opts=pulumi.ResourceOptions(
                parent=self,
            ),
        )

        self.configmap = k8s.core.v1.ConfigMap(
            resource_name=f'{resource_name}:configmap',
            metadata=k8s.meta.v1.ObjectMetaArgs(
                name=name,
                namespace=namespace,
                labels=labels,
            ),
            data={
                'install.yml': textwrap.dedent(f'''
                    # WebUI Admin definition
                    frontendlogin: {username}
                    frontendpassword: {password}

                    # DB connection
                    dbconnectiontype: tcp
                    dbtcphostname: {mariaDB.host}
                    dbtcpport: {mariaDB.port}
                    dbtcpname: {dbname}
                    dbtcpuser: {mariaDB.user}
                    dbtcppassword: {mariaDB.password}
                ''')
            },
            opts=pulumi.ResourceOptions(
                parent=self,
            ),
        )

        self.deploy = k8s.apps.v1.Deployment(
            f"{resource_name}:deploy",
            metadata=k8s.meta.v1.ObjectMetaArgs(
                name="pydio",
                namespace=namespace,
                labels=labels,
            ),
            spec=k8s.apps.v1.DeploymentSpecArgs(
                selector=k8s.meta.v1.LabelSelectorArgs(
                    match_labels=labels,
                ),
                template=k8s.core.v1.PodTemplateSpecArgs(
                    metadata=k8s.meta.v1.ObjectMetaArgs(
                        labels=labels,
                    ),
                    spec=k8s.core.v1.PodSpecArgs(
                        init_containers=[self.initdb.init_container],
                        containers=[
                            k8s.core.v1.ContainerArgs(
                                name="pydio",
                                image="pydio/cells:latest",
                                env=[
                                    k8s.core.v1.EnvVarArgs(
                                        name="CELLS_INSTALL_YAML",
                                        value="/pydio/config/install.yml",
                                    ),
                                    k8s.core.v1.EnvVarArgs(
                                        name="CELLS_BIND",
                                        value="0.0.0.0:80",
                                    ),
                                ],
                                ports=[
                                    k8s.core.v1.ContainerPortArgs(
                                        container_port=80,
                                        name="http",
                                    ),
                                ],
                                volume_mounts=[
                                    k8s.core.v1.VolumeMountArgs(
                                        name="cellsdir",
                                        mount_path="/var/cells",
                                    ),
                                    k8s.core.v1.VolumeMountArgs(
                                        name="pydio-install",
                                        mount_path="/pydio/config/install.yml",
                                        sub_path="install.yml",
                                    ),
                                ],
                            )
                        ],
                        volumes=[
                            k8s.core.v1.VolumeArgs(
                                name="cellsdir",
                                persistent_volume_claim=k8s.core.v1.PersistentVolumeClaimVolumeSourceArgs(
                                    claim_name=self.persistent_volume_claim.metadata["name"],
                                ),
                            ),
                            k8s.core.v1.VolumeArgs(
                                name="pydio-install",
                                config_map=k8s.core.v1.ConfigMapVolumeSourceArgs(
                                    name=self.configmap.metadata["name"],
                                ),
                            ),
                            self.initdb.volume,
                        ],
                    ),
                ),
            ),
            opts=pulumi.ResourceOptions(
                parent=self,
                depends_on=[self.persistent_volume_claim, self.initdb, self.configmap],
            ),
        )

        # Set up the nodeport
        if node_port is not None:
            http_port = k8s.core.v1.ServicePortArgs(
                name="http",
                port=80,
                target_port="http",
                node_port=node_port,
            )
            svc_type = "NodePort"
        else:
            http_port = k8s.core.v1.ServicePortArgs(
                name="http",
                port=80,
                target_port="http",
            )
            svc_type = "ClusterIP"


        # Create a service
        self.service = k8s.core.v1.Service(
            resource_name=f'{resource_name}:service',
            metadata=k8s.meta.v1.ObjectMetaArgs(
                name="pydio",
                namespace=namespace,
                labels=labels,
            ),
            spec=k8s.core.v1.ServiceSpecArgs(
                selector=labels,
                ports=[http_port],
                type=svc_type,
            ),
            opts=pulumi.ResourceOptions(
                parent=self,
                depends_on=[self.deploy],
            ),
        )
