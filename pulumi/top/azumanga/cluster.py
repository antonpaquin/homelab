from typing import Dict

import pulumi
from modules.app.homepage.impl import HomepageApp, HomepageGroup, HomepageInstallation
from modules.app.radarr.impl import RadarrInstallation
from modules.app.sabnzbd.impl import SabnzbdInstallation
from modules.app.sonarr.impl import SonarrInstallation

from modules.k8s_infra.nginx import NginxInstallation
from modules.k8s_infra.nfs_external import ExternalNfs
from modules.app_infra.mariadb import MariaDBInstallation
from modules.app_infra.routed_nginx import RoutedNginx, NginxPort
from modules.app_infra.postgres import PostgresInstallation

from modules.app.calibre import CalibreInstallation, CalibreWebInstallation
from modules.app.deluge import DelugeInstallation
from modules.app.filebrowser import FilebrowserInstallation
from modules.app.heimdall import HeimdallInstallation, HeimdallApp
from modules.app.jellyfin import JellyfinInstallation
from modules.app.kavita import KavitaInstallation
from modules.app.metube import MeTubeInstallation
from modules.app.omada_controller import OmadaControllerInstallation
from modules.app.overseerr import OverseerrInstallation
from modules.app.photoprism import PhotoprismInstallation
from modules.app.plex import PlexInstallation
from modules.app.pydio import PydioInstallation
from modules.app.readarr import ReadarrInstallation
from modules.app.samba import SambaInstallation
from modules.app.shell import ShellInstallation
from modules.app.vaultwarden import VaultwardenInstallation

from config import Ports, ClusterNode


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
        _external_access_ip = '10.10.10.3'
        _vpn_ip = '192.168.100.103'

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
            nfs_server=storage_node.ip_address,
            nfs_path='/osaka-zfs0/_cluster/mariadb',
            opts=pulumi.ResourceOptions(
                parent=self,
                depends_on=[self.nfs],
                custom_timeouts=_not_slow,
            ),
        )
        mariaDB_conn = self.mariaDB.get_connection()

        # self.postgresql = PostgresInstallation(
        #     resource_name='postgresql',
        #     name='postgresql',
        #     namespace='default',
        #     password=secrets['postgresql']['root_password'],
        #     storage_size='50Gi',
        #     opts=pulumi.ResourceOptions(
        #         parent=self,
        #         depends_on=[self.nfs],
        #         custom_timeouts=_not_slow,
        #     ),
        # )
        # postgres_conn = self.postgresql.get_connection()

        self.deluge = DelugeInstallation(
            resource_name='deluge',
            name='deluge',
            namespace='default',
            nfs_data_path='/osaka-zfs0/torrents',
            nfs_config_path='/osaka-zfs0/_cluster/deluge',
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

        self.sabnzbd = SabnzbdInstallation(
            resource_name='sabnzbd',
            name='sabnzbd',
            namespace='default',
            nfs_data_path='/osaka-zfs0/torrents',
            nfs_config_path='/osaka-zfs0/_cluster/sabnzbd',
            nfs_server=storage_node.ip_address,
            node_port=Ports.sabnzbd,
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
            nfs_server=storage_node.ip_address,
            nfs_config_path='/osaka-zfs0/_cluster/pydio',
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
            nfs_data_path='/osaka-zfs0',
            nfs_config_path='/osaka-zfs0/_cluster/shell',
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

        self.jellyfin = JellyfinInstallation(
            resource_name='jellyfin',
            name='jellyfin',
            nfs_server=storage_node.ip_address,
            nfs_config_path='/osaka-zfs0/_cluster/jellyfin/config',
            nfs_db_path='/osaka-zfs0/_cluster/jellyfin/db',
            nfs_media_path='/osaka-zfs0/library',
            namespace='default',
            node_port=Ports.jellyfin,
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

        self.overseerr = OverseerrInstallation(
            resource_name='overseerr',
            name='overseerr',
            namespace='default',
            nfs_server=storage_node.ip_address,
            nfs_config_path='/osaka-zfs0/_cluster/overseerr',
            node_port=Ports.overseerr,
            opts=pulumi.ResourceOptions(
                parent=self,
                depends_on=[self.nfs],
                custom_timeouts=_not_slow,
            ),
        )

        self.sonarr = SonarrInstallation(
            resource_name='sonarr',
            name='sonarr',
            namespace='default',
            nfs_server=storage_node.ip_address,
            nfs_config_path='/osaka-zfs0/_cluster/sonarr',
            nfs_ingest_path='/osaka-zfs0/torrents/complete',
            nfs_library_path='/osaka-zfs0/library/video/TV',
            node_port=Ports.sonarr,
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
            nfs_data_path='/osaka-zfs0/library/books',
            nfs_config_path='/osaka-zfs0/_cluster/calibre',
            node_port=Ports.calibre,
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
            nfs_server=storage_node.ip_address,
            nfs_calibre_path='/osaka-zfs0/_cluster/calibre',
            nfs_config_path='/osaka-zfs0/_cluster/calibre-web',
            password=secrets['calibre_web']['password'],
            node_port=Ports.calibre_web,
            opts=pulumi.ResourceOptions(
                parent=self,
                depends_on=[self.nfs, self.calibre],
                custom_timeouts=_not_slow,
            ),
        )

        self.kavita = KavitaInstallation(
            resource_name='kavita',
            name='kavita',
            namespace='default',
            nfs_server=storage_node.ip_address,
            nfs_data_path='/osaka-zfs0/library/books',
            nfs_config_path='/osaka-zfs0/_cluster/kavita',
            node_port=Ports.kavita,
            opts=pulumi.ResourceOptions(
                parent=self,
                depends_on=[self.nfs],
                custom_timeouts=_not_slow,
            ),
        )

        self.samba = SambaInstallation(
            resource_name='samba',
            name='samba',
            namespace='default',
            nfs_server=storage_node.ip_address,
            nfs_path='/osaka-zfs0',
            user_pass=secrets['samba']['logins'],
            opts=pulumi.ResourceOptions(
                parent=self,
                depends_on=[self.nfs],
                custom_timeouts=_not_slow,
            ),
        )

        self.vaultwarden = VaultwardenInstallation(
            resource_name='vaultwarden',
            name='vaultwarden',
            namespace='default',
            nfs_server=storage_node.ip_address,
            nfs_config_path='/osaka-zfs0/_cluster/vaultwarden',
            opts=pulumi.ResourceOptions(
                parent=self,
                depends_on=[self.nfs],
                custom_timeouts=_not_slow,
            ),
        )

        self.routed_nginx = RoutedNginx(
            resource_name='routed-nginx',
            name='nginx-ssl',
            namespace='default',
            ports=[
                NginxPort('vaultwarden', self.vaultwarden.cluster_local_address(), 80, Ports.vaultwarden),
            ],
            ssl_crt_data=secrets['ssl']['crt'],
            ssl_key_data=secrets['ssl']['key'],
            opts=pulumi.ResourceOptions(
                parent=self,
                depends_on=[self.nfs],
                custom_timeouts=_not_slow,
            ),
        )

        self.readarr = ReadarrInstallation(
            resource_name='readarr',
            name='readarr',
            namespace='default',
            node_port=Ports.readarr,
            nfs_books_path='/osaka-zfs0/library/books',
            nfs_downloads_path='/osaka-zfs0/torrents/complete',
            nfs_config_path='/osaka-zfs0/_cluster/readarr',
            nfs_server=storage_node.ip_address,
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
            nfs_server=storage_node.ip_address,
            nfs_config_path='/osaka-zfs0/_cluster/heimdall',
            node_port=Ports.heimdall,
            opts=pulumi.ResourceOptions(
                parent=self,
                depends_on=[self.nfs],
                custom_timeouts=_not_slow,
            ),
        )

        self.radarr = RadarrInstallation(
            resource_name='radarr',
            name='radarr',
            namespace='default',
            nfs_server=storage_node.ip_address,
            nfs_config_path='/osaka-zfs0/_cluster/radarr',
            nfs_ingest_path='/osaka-zfs0/torrents/complete',
            nfs_library_path='/osaka-zfs0/library/video/Movies',
            node_port=Ports.radarr,
            opts=pulumi.ResourceOptions(
                parent=self,
                depends_on=[self.nfs],
                custom_timeouts=_not_slow,
            ),
        )

        self.homepage = HomepageInstallation(
            resource_name='homepage_vpn',
            name='homepage-vpn',
            namespace='default',
            nfs_server=storage_node.ip_address,
            nfs_config_path='/osaka-zfs0/_cluster/homepage',
            node_port=Ports.homepage,
            apps=[
                HomepageGroup(
                    name='Media', 
                    services=[
                        HomepageApp(
                            name='Jellyfin',
                            url=f'http://{_vpn_ip}:{Ports.jellyfin}',
                            icon='jellyfin',
                            description='Media server',
                        ),
                        HomepageApp(
                            name='Plex',
                            url=f'http://{_vpn_ip}:{Ports.plex}',
                            icon='plex',
                            description='Media server',
                        ),
                        HomepageApp(
                            name='Photoprism',
                            url=f'http://{_vpn_ip}:{Ports.photoprism}',
                            icon='photoprism',
                            description='Photos app',
                        ),
                        HomepageApp(
                            name='Filebrowser',
                            url=f'http://{_vpn_ip}:{Ports.filebrowser}',
                            icon='filebrowser',
                            description='Raw library access',
                        ),
                    ],
                ),
                HomepageGroup(
                    name='Video Library',
                    services=[
                        HomepageApp(
                            name='Sonarr',
                            url=f'http://{_vpn_ip}:{Ports.sonarr}',
                            icon='sonarr',
                            description='TV fetcher',
                        ),
                        HomepageApp(
                            name='Radarr',
                            url=f'http://{_vpn_ip}:{Ports.radarr}',
                            icon='radarr',
                            description='Movie fetcher',
                        ),
                        HomepageApp(
                            name='Metube',
                            url=f'http://{_vpn_ip}:{Ports.metube}',
                            icon='metube',
                            description='Youtube-dl interface',
                        ),
                        HomepageApp(
                            name='Overseerr',
                            url=f'http://{_vpn_ip}:{Ports.overseerr}',
                            icon='overseerr',
                            description='Request TV / movies',
                        ),
                    ]
                ),
                HomepageGroup(
                    name='Download Clients',
                    services=[
                        HomepageApp(
                            name='Deluge',
                            url=f'http://{_vpn_ip}:{Ports.deluge}',
                            icon='deluge',
                            description='Torrent client',
                        ),
                        HomepageApp(
                            name='SABNzbd',
                            url=f'http://{_vpn_ip}:{Ports.sabnzbd}',
                            icon='sabnzbd',
                            description='Usenet newsreader',
                        ),
                    ]
                ),
                HomepageGroup(
                    name='Books',
                    services=[
                        HomepageApp(
                            name='Calibre',
                            url=f'http://{_vpn_ip}:{Ports.calibre}',
                            icon='calibre',
                            description='Ebook program',
                        ),
                        HomepageApp(
                            name='Calibre-Web',
                            url=f'http://{_vpn_ip}:{Ports.calibre_web}',
                            icon='calibre-web',
                            description='Does something with calibre?',
                        ),
                        HomepageApp(
                            name='Readarr',
                            url=f'http://{_vpn_ip}:{Ports.readarr}',
                            icon='readarr',
                            description='Book fetcher',
                        ),
                        HomepageApp(
                            name='Kavita',
                            url=f'http://{_vpn_ip}:{Ports.kavita}',
                            icon='kavita',
                            description='Manga reader',
                        ),
                    ]
                ),
                HomepageGroup(
                    name='Admin',
                    services=[
                        # scrutiny: not available from vpn
                        # opnsense: not available from vpn
                        HomepageApp(
                            name='Omada Controller',
                            url=f'http://{_vpn_ip}:{Ports.omada_controller}',
                            icon='omada',
                            description='Wifi control',
                        ),
                        HomepageApp(
                            name='Vaultwarden',
                            url=f'http://{_vpn_ip}:{Ports.vaultwarden}',
                            icon='vaultwarden',
                            description='Password manager',
                        ),
                    ]
                )
            ],
            opts=pulumi.ResourceOptions(
                parent=self,
                depends_on=[self.nfs],
                custom_timeouts=_not_slow,
            ),
        )

        self.omada_controller = OmadaControllerInstallation(
            resource_name='omada-controller',
            name='omada-controller',
            namespace='default',
            nfs_server=storage_node.ip_address,
            nfs_path='/osaka-zfs0/_cluster/omada-controller',
            node_port=Ports.omada_controller,
            opts=pulumi.ResourceOptions(
                parent=self,
                depends_on=[self.nfs],
                custom_timeouts=_not_slow,
            ),
        )
