"""A Python Pulumi program"""

from typing import Dict

import pulumi

from modules.lib.config_types import ClusterNode
from modules.k8s_infra.nginx import create_nginx, NginxInstallation
from modules.k8s_infra.nfs_external import create_external_nfs, ExternalNfs


class Nodes:
    yomi = ClusterNode(
        name='yomi', 
        ip_address='10.10.10.1'
    )
    chiyo = ClusterNode(
        name='chiyo',
        ip_address='10.10.10.2'
    )
    sakaki = ClusterNode(
        name='sakaki',
        ip_address='10.10.10.3'
    )
    osaka = ClusterNode(
        name='osaka',
        ip_address='10.10.10.4'
    )


class AzumangaCluster:
    nginx: NginxInstallation
    externalNfs: ExternalNfs

    def __init__(
        self,
        nginx: NginxInstallation,
        nfs: ExternalNfs,
    ) -> None:
        self.nginx = nginx
        self.nfs = nfs


def create_azumanga() -> AzumangaCluster:
    return AzumangaCluster(
        nginx=create_nginx(),
        nfs=create_external_nfs(namespace='kube-system', pvc_storage_path='/osaka-zfs0/_cluster/k8s-pvc', node_ip=Nodes.osaka.ip_address),
    )


pulumi.export("azumanga", create_azumanga())
