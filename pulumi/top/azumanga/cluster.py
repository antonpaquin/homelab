from typing import Dict

import pulumi

from modules.k8s_infra.nginx import NginxInstallation
from modules.k8s_infra.nfs_external import ExternalNfs
from modules.app_infra.mariadb import MariaDBInstallation

from modules.app.calibre import CalibreInstallation, CalibreWebInstallation
from modules.app.deluge import DelugeInstallation
from modules.app.filebrowser import FilebrowserInstallation
from modules.app.heimdall import HeimdallInstallation, HeimdallApp
from modules.app.kavita import KavitaInstallation
from modules.app.metube import MeTubeInstallation
from modules.app.overseerr import OverseerrInstallation
from modules.app.photoprism import PhotoprismInstallation
from modules.app.plex import PlexInstallation
from modules.app.pydio import PydioInstallation
from modules.app.shell import ShellInstallation

from config import Nodes, Ports, ClusterNode


class AzumangaCluster(pulumi.ComponentResource):
    nginx: NginxInstallation
    externalNfs: ExternalNfs
    deluge: DelugeInstallation
    mariaDB: MariaDBInstallation
    pydio: PydioInstallation
    shell: ShellInstallation
    photoprism: PhotoprismInstallation
    filebrowser: FilebrowserInstallation

    def __init__(
        self,
        secrets: dict,
        storage_node: ClusterNode,
    ) -> None:
        super().__init__('anton:cluster:azumanga', 'azumanga', None, None)

        _not_slow = pulumi.CustomTimeouts(create='30s')
        _external_access_ip = '10.0.3.105'

        self.nginx = NginxInstallation(
            resource_name='nginx',
            opts=pulumi.ResourceOptions(parent=self),
        )

        self.nfs = ExternalNfs(
            resource_name='nfs',
            namespace='kube-system',
            name='nfs-external-subdir',
            storage_class_name='nfs-client',
            storage_node_ip=storage_node.ip_address,
            pvc_storage_path='/osaka-zfs0/_cluster/k8s-pvc',
            opts=pulumi.ResourceOptions(
                parent=self,
                custom_timeouts=_not_slow,
            ),
        )

        self.mariaDB = MariaDBInstallation(
            resource_name='mariadb',
            name='mariadb',
            namespace='default',
            password=secrets['mariadb']['root_password'],
            storage_size='50Gi',
            opts=pulumi.ResourceOptions(
                parent=self,
                depends_on=[self.nfs],
                custom_timeouts=_not_slow,
            ),
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
            opts=pulumi.ResourceOptions(
                parent=self,
                depends_on=[self.nfs],
                custom_timeouts=_not_slow,
            ),
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
            opts=pulumi.ResourceOptions(
                parent=self,
                depends_on=[self.mariaDB],
                custom_timeouts=_not_slow,
            ),
        )

        self.pydio = PydioInstallation(
            resource_name='pydio',
            name='pydio',
            namespace='default',
            username=secrets['pydio']['username'],
            password=secrets['pydio']['password'],
            mariaDB=mariaDB_conn,
            node_port=Ports.pydio,
            opts=pulumi.ResourceOptions(
                parent=self,
                depends_on=[self.mariaDB],
                custom_timeouts=_not_slow,

            ),
        )

        self.shell = ShellInstallation(
            resource_name='shell',
            name='shell',
            namespace='default',
            nfs_server=storage_node.ip_address,
            nfs_path='/osaka-zfs0',
            opts=pulumi.ResourceOptions(
                parent=self,
                depends_on=[self.nfs],
                custom_timeouts=_not_slow,
            ),
        )

        self.filebrowser = FilebrowserInstallation(
            resource_name='filebrowser',
            name='filebrowser',
            namespace='default',
            nfs_server=storage_node.ip_address,
            nfs_path='/osaka-zfs0',
            node_port=Ports.filebrowser,
            opts=pulumi.ResourceOptions(
                parent=self,
                depends_on=[self.nfs],
                custom_timeouts=_not_slow,
            ),
        )

        self.plex = PlexInstallation(
            resource_name='plex',
            name='plex',
            namespace='default',
            nfs_server=storage_node.ip_address,
            nfs_path='/osaka-zfs0/library',
            external_ip=_external_access_ip,
            node_port=Ports.plex,
            opts=pulumi.ResourceOptions(
                parent=self,
                depends_on=[self.nfs],
                custom_timeouts=_not_slow,
            ),
        )

        self.metube = MeTubeInstallation(
            resource_name='metube',
            name='metube',
            namespace='default',
            nfs_server=storage_node.ip_address,
            nfs_path='/osaka-zfs0/ingest',
            node_port=Ports.metube,
            opts=pulumi.ResourceOptions(
                parent=self,
                depends_on=[self.nfs],
                custom_timeouts=_not_slow,
            ),
        )

        self.calibre = CalibreInstallation(
            resource_name='calibre',
            name='calibre',
            namespace='default',
            nfs_server=storage_node.ip_address,
            nfs_path='/osaka-zfs0/library/books',
            node_port=Ports.calibre,
            password=secrets['calibre']['password'],
            opts=pulumi.ResourceOptions(
                parent=self,
                depends_on=[self.nfs],
                custom_timeouts=_not_slow,
            ),
        )

        self.calibre_web = CalibreWebInstallation(
            resource_name='calibre-web',
            name='calibre-web',
            namespace='default',
            calibre_pvc=self.calibre.persistent_volume_claim,
            password=secrets['calibre_web']['password'],
            node_port=Ports.calibre_web,
            opts=pulumi.ResourceOptions(
                parent=self,
                depends_on=[self.nfs, self.calibre],
                custom_timeouts=_not_slow,
            ),
        )

        self.overseerr = OverseerrInstallation(
            resource_name='overseerr',
            name='overseerr',
            namespace='default',
            node_port=Ports.overseerr,
            opts=pulumi.ResourceOptions(
                parent=self,
                depends_on=[self.nfs],
                custom_timeouts=_not_slow,
            ),
        )

        self.kavita = KavitaInstallation(
            resource_name='kavita',
            name='kavita',
            namespace='default',
            nfs_server=storage_node.ip_address,
            nfs_path='/osaka-zfs0/library/books',
            node_port=Ports.kavita,
            opts=pulumi.ResourceOptions(
                parent=self,
                depends_on=[self.nfs],
                custom_timeouts=_not_slow,
            ),
        )

        self.heimdall = HeimdallInstallation(
            resource_name='heimdall',
            name='heimdall',
            namespace='default',
            # apps=[
            #     HeimdallApp(name='deluge', url=f'http://{_external_access_ip}:{Ports.deluge}'),
            #     HeimdallApp(name='photoprism', url=f'http://{_external_access_ip}:{Ports.photoprism}'),
            #     HeimdallApp(name='pydio', url=f'http://{_external_access_ip}:{Ports.pydio}'),
            #     HeimdallApp(name='filebrowser', url=f'http://{_external_access_ip}:{Ports.filebrowser}'),
            #     HeimdallApp(name='plex', url=f'http://{_external_access_ip}:{Ports.plex}'),
            # ],
            node_port=Ports.heimdall,
            opts=pulumi.ResourceOptions(
                parent=self,
                depends_on=[self.nfs],
                custom_timeouts=_not_slow,
            ),
        )


