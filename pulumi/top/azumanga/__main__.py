"""A Python Pulumi program"""

from typing import Dict

import pulumi

from modules.lib.config_types import ClusterNode
from modules.k8s_infra.nginx import create_nginx, NginxInstallation


nodes: Dict[str, ClusterNode] = {
    'yomi': ClusterNode(
        name='yomi', 
        ip_address='10.10.10.1'
    ),
    'chiyo': ClusterNode(
        name='chiyo',
        ip_address='10.10.10.2'
    ),
    'sakaki': ClusterNode(
        name='sakaki',
        ip_address='10.10.10.3'
    ),
    'osaka': ClusterNode(
        name='osaka',
        ip_address='10.10.10.4'
    ),
}

class AzumangaCluster:
    nginx: NginxInstallation

    def __init__(
        self,
        nginx: NginxInstallation
    ) -> None:
        self.nginx = nginx


def create_azumanga() -> AzumangaCluster:
    return AzumangaCluster(
        nginx=create_nginx(),
    )


pulumi.export("azumanga", create_azumanga())


# module "nfs" {
#   source = "../../../modules/k8s_infra/nfs-external"
#   nfs_node_ip = local.osaka_ip
# }