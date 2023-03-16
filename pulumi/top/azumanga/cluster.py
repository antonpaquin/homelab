from typing import Dict

import pulumi
import yaml

from modules.k8s_infra.nginx import NginxInstallation
from modules.k8s_infra.nfs_external import ExternalNfs
from modules.app_infra.mariadb import MariaDBInstallation

from modules.app.deluge import DelugeInstallation
from modules.app.pydio import PydioInstallation
from modules.app.shell import ShellInstallation
from modules.app.photoprism import PhotoprismInstallation

from config import Nodes, Ports, ClusterNode


class AzumangaCluster(pulumi.ComponentResource):
    nginx: NginxInstallation
    externalNfs: ExternalNfs
    deluge: DelugeInstallation
    mariaDB: MariaDBInstallation
    pydio: PydioInstallation
    shell: ShellInstallation
    photoprism: PhotoprismInstallation

    def __init__(
        self,
        secrets: dict,
        storage_node: ClusterNode,
    ) -> None:
        super().__init__('anton:cluster:azumanga', 'azumanga', None, None)

        self.nginx = NginxInstallation(
            resource_name='nginx',
        )

        self.mariaDB = MariaDBInstallation(
            resource_name='mariadb',
            name='mariadb',
            namespace='default',
            password=secrets['mariadb']['root_password'],
            storage_size='50Gi',
        )
        mariaDB_conn = self.mariaDB.get_connection()

        self.deluge = DelugeInstallation(
            resource_name='deluge',
            name='deluge',
            namespace='default',
            nfs_path='/osaka-zfs0/torrents',
            nfs_server=storage_node.ip_address,
            username=secrets['deluge']['username'],
            password=secrets['deluge']['password'],
            max_download_speed_kb='80',
            max_upload_speed_kb='5',
            node_port=Ports.deluge,
        )

        self.photoprism = PhotoprismInstallation(
            resource_name='photoprism',
            name='photoprism',
            namespace='default',
            password=secrets['photoprism']['password'],
            db_connection=mariaDB_conn,
            nfs_server=storage_node.ip_address,
            nfs_photos_path='/osaka-zfs0/library/photos',
            nfs_imports_path='/osaka-zfs0/_cluster/photoprism/import',
            nfs_exports_path='/osaka-zfs0/_cluster/photoprism/export',
            nodeport=Ports.photoprism,
        )

        self.pydio = PydioInstallation(
            resource_name='pydio',
            name='pydio',
            namespace='default',
            nfs_path='/osaka-zfs0/library',
            nfs_server_ip=storage_node.ip_address,
            username=secrets['pydio']['username'],
            password=secrets['pydio']['password'],
            mariaDB=mariaDB_conn,
            node_port=Ports.pydio,
        )

        self.shell = ShellInstallation(
            resource_name='shell',
            name='shell',
            namespace='default',
            nfs_server=storage_node.ip_address,
            nfs_path='/osaka-zfs0',
        )

        self.nfs = ExternalNfs(
            resource_name='nfs',
            namespace='kube-system',
            name='nfs-external-subdir',
            storage_class_name='nfs-client',
            storage_node_ip=storage_node.ip_address,
            pvc_storage_path='/osaka-zfs0/_cluster/k8s-pvc',
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