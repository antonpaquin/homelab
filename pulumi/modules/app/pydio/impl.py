import textwrap

import pulumi_kubernetes as k8s

from .head import PydioInstallation

from modules.lib.boilerplate import simple_configmap
from modules.lib.config_types import MariaDBConnection


def create_pydio(
    nfs_path: str, 
    nfs_server_ip: str, 
    username: str,
    password: str,
    mariaDB: MariaDBConnection,
    node_port: int | None = None, 
    namespace: str | None = None
) -> PydioInstallation:
    if namespace is None:
        namespace = "default"

    dbname = 'cells'

    pvc = k8s.core.v1.PersistentVolumeClaim(
        "kubernetes-persistentvolumeclaim-default-pydio",
        metadata=k8s.meta.v1.ObjectMetaArgs(
            name="pydio",
            namespace=namespace,
            labels={"app": "pydio"},
        ),
        spec=k8s.core.v1.PersistentVolumeClaimSpecArgs(
            access_modes=["ReadWriteOnce"],
            resources=k8s.core.v1.ResourceRequirementsArgs(
                requests={"storage": "2Gi"},
            ),
            storage_class_name="nfs-client",
        ),
    )

    cm = simple_configmap('pydio-install', namespace=namespace, contents={
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
    })

    # Create a deployment
    deploy = k8s.apps.v1.Deployment(
        "kubernetes-deployment-default-pydio",
        metadata=k8s.meta.v1.ObjectMetaArgs(
            name="pydio",
            namespace=namespace,
            labels={"app": "pydio"},
        ),
        spec=k8s.apps.v1.DeploymentSpecArgs(
            selector=k8s.meta.v1.LabelSelectorArgs(
                match_labels={"app": "pydio"},
            ),
            template=k8s.core.v1.PodTemplateSpecArgs(
                metadata=k8s.meta.v1.ObjectMetaArgs(
                    labels={"app": "pydio"},
                ),
                spec=k8s.core.v1.PodSpecArgs(
                    containers=[
                        k8s.core.v1.ContainerArgs(
                            name="pydio",
                            image="pydio/cells:latest",
                            env=[
                                k8s.core.v1.EnvVarArgs(
                                    name="CELLS_INSTALL_YAML",
                                    value="/pydio/config/install.yml",
                                ),
                            ],
                            ports=[
                                k8s.core.v1.ContainerPortArgs(
                                    container_port=8080,
                                ),
                            ],
                            volume_mounts=[
                                k8s.core.v1.VolumeMountArgs(
                                    name="cellsdir",
                                    mount_path="/var/cells",
                                ),
                                k8s.core.v1.VolumeMountArgs(
                                    name="data",
                                    mount_path="/var/cells/data",
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
                                claim_name=pvc.metadata["name"],
                            ),
                        ),
                        k8s.core.v1.VolumeArgs(
                            name="data",
                            nfs=k8s.core.v1.NFSVolumeSourceArgs(
                                server=nfs_server_ip,
                                path=nfs_path,
                            ),
                        ),
                        k8s.core.v1.VolumeArgs(
                            name="pydio-install",
                            config_map=k8s.core.v1.ConfigMapVolumeSourceArgs(
                                name=cm.metadata["name"],
                            ),
                        ),
                    ],
                ),
            ),
        ),
    )

    # Set up the nodeport
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


    # Create a service
    service = k8s.core.v1.Service(
        "pydio-service",
        spec=k8s.core.v1.ServiceSpecArgs(
            selector={"app": "pydio"},
            ports=[
                http_port,
            ],
            type=svc_type,
        ),
    )

    return PydioInstallation(pvc=pvc, deploy=deploy, service=service)
