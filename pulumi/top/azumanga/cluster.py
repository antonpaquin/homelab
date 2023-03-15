from typing import Dict

import yaml

from modules.k8s_infra.nginx import create_nginx, NginxInstallation
from modules.k8s_infra.nfs_external import create_external_nfs, ExternalNfs
from modules.app_infra.mariadb import create_mariadb, MariaDBInstallation

from modules.app.deluge import create_deluge, DelugeInstallation
from modules.app.pydio import create_pydio, PydioInstallation
from modules.app.shell import create_shell, ShellInstallation
from modules.app.photoprism import create_photoprism, PhotoprismInstallation

from modules.lib.boilerplate import cluster_local_address
from modules.lib.config_types import MariaDBConnection

from config import Nodes, Ports


class AzumangaCluster:
    nginx: NginxInstallation
    externalNfs: ExternalNfs
    deluge: DelugeInstallation
    mariaDB: MariaDBInstallation
    pydio: PydioInstallation
    shell: ShellInstallation
    photoprism: PhotoprismInstallation

    def __init__(
        self,
        nginx: NginxInstallation,
        nfs: ExternalNfs,
        deluge: DelugeInstallation,
        mariaDB: MariaDBInstallation,
        pydio: PydioInstallation,
        shell: ShellInstallation,
        photoprism: PhotoprismInstallation,
    ) -> None:
        self.nginx = nginx
        self.nfs = nfs
        self.deluge = deluge
        self.mariaDB = mariaDB
        self.pydio = pydio
        self.shell = shell
        self.photoprism = photoprism


def create_azumanga(secrets: Dict) -> AzumangaCluster:
    storage_node = Nodes.osaka

    mariaDB = create_mariadb(
        namespace='default',
        password=secrets['mariadb']['root_password'],
        storage_size='50Gi',
    )

    mariaDB_conn = MariaDBConnection(
        host=cluster_local_address(mariaDB.service_name, mariaDB.namespace),
        port=mariaDB.port,
        user=mariaDB.user,
        password=mariaDB.password,
    )

    return AzumangaCluster(
        nginx=create_nginx(),
        nfs=create_external_nfs(
            namespace='kube-system', 
            pvc_storage_path='/osaka-zfs0/_cluster/k8s-pvc', 
            node_ip=storage_node.ip_address,
        ),
        deluge=create_deluge(
            namespace='default',
            nfs_path='/osaka-zfs0/torrents',
            nfs_server=storage_node.ip_address,
            username=secrets['deluge']['username'],
            password=secrets['deluge']['password'],
            max_download_speed_kb='80',
            max_upload_speed_kb='5',
            node_port=Ports.deluge,
        ),
        mariaDB=mariaDB,
        pydio=create_pydio(
            namespace='default',
            nfs_path='/osaka-zfs0/library',
            nfs_server_ip=storage_node.ip_address,
            username=secrets['pydio']['username'],
            password=secrets['pydio']['password'],
            mariaDB=mariaDB_conn,
            node_port=Ports.pydio,
        ),
        shell=create_shell(
            namespace='default',
            nfs_path='/osaka-zfs0',
            nfs_server=storage_node.ip_address,
        ),
        photoprism=create_photoprism(
            namespace='default',
            password=secrets['photoprism']['password'],
            db_connection=mariaDB_conn,
            nfs_server=storage_node.ip_address,
            nfs_photos_path='/osaka-zfs0/library/photos',
            nfs_imports_path='/osaka-zfs0/_cluster/photoprism/import',
            nfs_exports_path='/osaka-zfs0/_cluster/photoprism/export',
            nodeport=Ports.photoprism,
        ),
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