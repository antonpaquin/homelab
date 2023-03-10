"""A Python Pulumi program"""

from typing import Dict

import pulumi
import yaml


from modules.lib.pulumi_model import PulumiModel
from modules.lib.config_types import ClusterNode

from modules.k8s_infra.nginx import create_nginx, NginxInstallation
from modules.k8s_infra.nfs_external import create_external_nfs, ExternalNfs

from modules.app.deluge import create_deluge, DelugeInstallation


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


class AzumangaCluster(PulumiModel):
    nginx: NginxInstallation
    externalNfs: ExternalNfs
    deluge: DelugeInstallation

    def __init__(
        self,
        nginx: NginxInstallation,
        nfs: ExternalNfs,
        deluge: DelugeInstallation
    ) -> None:
        self.nginx = nginx
        self.nfs = nfs
        self.deluge = deluge

    def export(self, prefix: str):
        self.nginx.export(f"{prefix}.nginx")
        self.nfs.export(f"{prefix}.nfs")
        self.deluge.export(f"{prefix}.deluge")


def create_azumanga() -> AzumangaCluster:
    with open('secret.yaml', 'r') as in_f:
        secrets = yaml.safe_load(in_f)

    return AzumangaCluster(
        nginx=create_nginx(),
        nfs=create_external_nfs(
            namespace='kube-system', 
            pvc_storage_path='/osaka-zfs0/_cluster/k8s-pvc', 
            node_ip=Nodes.osaka.ip_address,
        ),
        deluge=create_deluge(
            nfs_path='/osaka-zfs0/torrents',
            nfs_server=Nodes.osaka.ip_address,
            username=secrets['deluge']['username'],
            password=secrets['deluge']['password'],
            max_download_speed_kb='80',
            max_upload_speed_kb='5',
        )
    )

# module "filebrowser" {
#   source = "../../../modules/app/filebrowser"
#   authproxy_host = module.authproxy-default.host
#   media-pvc = module.volumes.media-claim-name
#   domain = local.domain
#   tls_secret = local.tls_secrets.default.name
# }
# 
# module "metube" {
#   source = "../../../modules/app/metube"
#   authproxy_host = module.authproxy-default.host
#   domain = local.domain
#   media-pvc = module.volumes.media-claim-name
#   tls_secret = local.tls_secrets.default.name
# }
# 
# module "photoprism" {
#   depends_on = [module.mariadb]
#   source = "../../../modules/app/photoprism"
#   domain = local.domain
#   authproxy_host = module.authproxy-default.host
#   database = {
#     username = module.mariadb.user
#     password = module.mariadb.password
#     host = module.mariadb.service
#     port = module.mariadb.port
#     dbname = "photoprism"
#   }
#   media-pvc = module.volumes.media-claim-name
#   tls_secret = local.tls_secrets.default.name
# }
# 
# module "shell" {
#   source = "../../../modules/app/shell"
#   media-pvc = module.volumes.media-claim-name
#   backup-pvc = module.volumes.backup-claim-name
# }

azumanga = create_azumanga()
azumanga.export('azumanga')
