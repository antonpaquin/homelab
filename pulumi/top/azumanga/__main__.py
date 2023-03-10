"""A Python Pulumi program"""

from typing import Dict

import pulumi

from modules.lib.config_types import ClusterNode
from modules.k8s_infra.nginx import create_nginx


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

nginx = create_nginx()


pulumi.export("nginx", nginx)


# module "nfs" {
#   source = "../../../modules/k8s_infra/nfs-external"
#   nfs_node_ip = local.osaka_ip
# }