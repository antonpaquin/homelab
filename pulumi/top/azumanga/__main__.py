"""A Python Pulumi program"""

from typing import Dict

import pulumi
from pulumi_kubernetes.apps.v1 import Deployment, DeploymentSpecArgs
from pulumi_kubernetes.meta.v1 import LabelSelectorArgs, ObjectMetaArgs
from pulumi_kubernetes.core.v1 import ContainerArgs, PodSpecArgs, PodTemplateSpecArgs


class ClusterNode:
    name: str
    ip_address: str

    def __init__(self, name: str, ip_address: str) -> None:
        self.name = name
        self.ip_address = ip_address


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

app_labels = { "app": "nginx" }


deployment = Deployment(
    "nginx",
    spec=DeploymentSpecArgs(
        selector=LabelSelectorArgs(match_labels=app_labels),
        replicas=1,
        template=PodTemplateSpecArgs(
            metadata=ObjectMetaArgs(labels=app_labels),
            spec=PodSpecArgs(containers=[ContainerArgs(name="nginx", image="nginx")])
        ),
    ))


pulumi.export("name", deployment.metadata["name"])


# locals {
#   yomi_ip   = "10.10.10.1"
#   chiyo_ip  = "10.10.10.2"
#   sakaki_ip = "10.10.10.3"
#   osaka_ip  = "10.10.10.4"
# }
# 
# module "nfs" {
#   source = "../../../modules/k8s_infra/nfs-external"
#   nfs_node_ip = local.osaka_ip
# }
# 
# module "nginx" {
#   source = "../../../modules/k8s_infra/nginx"
# }
# 