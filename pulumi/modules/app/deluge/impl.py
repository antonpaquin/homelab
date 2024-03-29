import hashlib
import textwrap

import pulumi
import pulumi_kubernetes as k8s

from modules.lib.boilerplate import simple_env_vars, config_map_volume


class DelugeInstallation(pulumi.ComponentResource):
    persistent_volume_claim: k8s.core.v1.PersistentVolumeClaim
    configmap: k8s.core.v1.ConfigMap
    deploy: k8s.apps.v1.Deployment
    service: k8s.core.v1.Service

    def __init__(
        self, 
        resource_name: str, 
        name: str,
        nfs_data_path: str, 
        nfs_config_path: str,
        nfs_server: str,
        username: str,
        password: str,
        max_upload_speed_kb: str,
        max_download_speed_kb: str,
        namespace: str | None = None,
        node_port: int | None = None,
        opts: pulumi.ResourceOptions | None = None
    ) -> None:
        super().__init__('anton:app:deluge', resource_name, None, opts)

        if namespace is None:
            namespace = "default"

        _labels = {'app': 'deluge'}

        pwd_salt = "ee41e8fd8504c493ed4825491e86b7b27acf5ec1"
        pwd_digest = hashlib.sha1()
        pwd_digest.update(pwd_salt.encode('utf-8'))
        pwd_digest.update(password.encode('utf-8'))
        pwd_hash = pwd_digest.hexdigest()

        self.configmap = k8s.core.v1.ConfigMap(
            resource_name=f'{resource_name}:configmap',
            metadata=k8s.meta.v1.ObjectMetaArgs(
                name=name,
                namespace=namespace,
            ),
            data={
                'core.conf': textwrap.dedent('''
                    {
                        "file": 1,
                        "format": 1
                    }{
                        "add_paused": false,
                        "allow_remote": false,
                        "auto_manage_prefer_seeds": false,
                        "auto_managed": true,
                        "cache_expiry": 60,
                        "cache_size": 512,
                        "copy_torrent_file": false,
                        "daemon_port": 58846,
                        "del_copy_torrent_file": false,
                        "dht": true,
                        "dont_count_slow_torrents": false,
                        "download_location": "/torrents/progress",
                        "download_location_paths_list": [],
                        "enabled_plugins": [],
                        "enc_in_policy": 1,
                        "enc_level": 2,
                        "enc_out_policy": 1,
                        "geoip_db_location": "/usr/share/GeoIP/GeoIP.dat",
                        "ignore_limits_on_local_network": true,
                        "info_sent": 0.0,
                        "listen_interface": "",
                        "listen_ports": [
                            6881,
                            6891
                        ],
                        "listen_random_port": 52711,
                        "listen_reuse_port": true,
                        "listen_use_sys_port": false,
                        "lsd": true,
                        "max_active_downloading": 3,
                        "max_active_limit": 8,
                        "max_active_seeding": 5,
                        "max_connections_global": 200,
                        "max_connections_per_second": 20,
                        "max_connections_per_torrent": -1,
                        "max_download_speed": ''' + max_download_speed_kb + ''',
                        "max_download_speed_per_torrent": -1,
                        "max_half_open_connections": 50,
                        "max_upload_slots_global": 4,
                        "max_upload_slots_per_torrent": -1,
                        "max_upload_speed": ''' + max_upload_speed_kb + ''',
                        "max_upload_speed_per_torrent": -1,
                        "move_completed": true,
                        "move_completed_path": "/torrents/complete",
                        "move_completed_paths_list": [],
                        "natpmp": true,
                        "new_release_check": false,
                        "outgoing_interface": "",
                        "outgoing_ports": [
                            0,
                            0
                        ],
                        "path_chooser_accelerator_string": "Tab",
                        "path_chooser_auto_complete_enabled": true,
                        "path_chooser_max_popup_rows": 20,
                        "path_chooser_show_chooser_button_on_localhost": true,
                        "path_chooser_show_hidden_files": false,
                        "peer_tos": "0x00",
                        "plugins_location": "/config/plugins",
                        "pre_allocate_storage": false,
                        "prioritize_first_last_pieces": false,
                        "proxy": {
                            "anonymous_mode": false,
                            "force_proxy": false,
                            "hostname": "",
                            "password": "",
                            "port": 8080,
                            "proxy_hostnames": true,
                            "proxy_peer_connections": true,
                            "proxy_tracker_connections": true,
                            "type": 0,
                            "username": ""
                        },
                        "queue_new_to_top": false,
                        "random_outgoing_ports": true,
                        "random_port": true,
                        "rate_limit_ip_overhead": true,
                        "remove_seed_at_ratio": false,
                        "seed_time_limit": 180,
                        "seed_time_ratio_limit": 7.0,
                        "send_info": false,
                        "sequential_download": false,
                        "share_ratio_limit": 2.0,
                        "shared": false,
                        "stop_seed_at_ratio": false,
                        "stop_seed_ratio": 2.0,
                        "super_seeding": false,
                        "torrentfiles_location": "/torrents/torrentfiles",
                        "upnp": true,
                        "utpex": true
                    }
                '''),
                'auth': textwrap.dedent(f'''
                    localclient:cf1bf6ad72a65a6cc7dd053ee0643007d56a392b:10
                    {username}:{password}:10
                '''),
                'web.conf': textwrap.dedent('''
                    {
                        "file": 2,
                        "format": 1
                    }{
                        "base": "/",
                        "cert": "ssl/daemon.cert",
                        "default_daemon": "",
                        "enabled_plugins": ["label"],
                        "first_login": false,
                        "https": false,
                        "interface": "0.0.0.0",
                        "language": "",
                        "pkey": "ssl/daemon.pkey",
                        "port": 8112,
                        "pwd_salt": "''' + pwd_salt + '''",
                        "pwd_sha1": "''' + pwd_hash + '''",
                        "session_timeout": 3600,
                        "sessions": {},
                        "show_session_speed": false,
                        "show_sidebar": true,
                        "sidebar_multiple_filters": true,
                        "sidebar_show_zero": false,
                        "theme": "gray"
                    }
                ''')
            },
            opts=pulumi.ResourceOptions(
                parent=self,
            ),
        )

        self.deploy = k8s.apps.v1.Deployment(
            resource_name=f'{resource_name}:deploy',
            metadata=k8s.meta.v1.ObjectMetaArgs(
                name=name,
                namespace=namespace,
            ),
            spec=k8s.apps.v1.DeploymentSpecArgs(
                selector=k8s.meta.v1.LabelSelectorArgs(match_labels=_labels),
                template=k8s.core.v1.PodTemplateSpecArgs(
                    metadata=k8s.meta.v1.ObjectMetaArgs(labels=_labels),
                    spec=k8s.core.v1.PodSpecArgs(
                        containers=[
                            k8s.core.v1.ContainerArgs(
                                name="main",
                                image="ghcr.io/linuxserver/deluge",
                                env=simple_env_vars({
                                    'PUID': '1000',
                                    'PGID': '1000',
                                    'TZ': 'US/Pacific',
                                }),
                                volume_mounts=[
                                    k8s.core.v1.VolumeMountArgs(mount_path='/torrents', name='torrents'),
                                    k8s.core.v1.VolumeMountArgs(mount_path='/config/core.conf', name='config-file', sub_path='core.conf'),
                                    k8s.core.v1.VolumeMountArgs(mount_path='/config/auth', name='config-file', sub_path='auth'),
                                    k8s.core.v1.VolumeMountArgs(mount_path='/config/web.conf', name='config-file', sub_path='web.conf'),
                                ]
                            ),
                        ],
                        volumes=[
                            k8s.core.v1.VolumeArgs(name='torrents', nfs=k8s.core.v1.NFSVolumeSourceArgs(path=nfs_data_path, server=nfs_server)),
                            k8s.core.v1.VolumeArgs(name='config', nfs=k8s.core.v1.NFSVolumeSourceArgs(path=nfs_config_path, server=nfs_server)),
                            config_map_volume('config-file', self.configmap),
                        ]
                    )
                ),
            ),
            opts=pulumi.ResourceOptions(
                parent=self,
                depends_on=[self.configmap],
            ),
        )

        if node_port is not None:
            http_port = k8s.core.v1.ServicePortArgs(name='http', port=80, target_port=8112, node_port=node_port)
            svc_type = 'NodePort'
        else:
            http_port = k8s.core.v1.ServicePortArgs(name='http', port=80, target_port=8112)
            svc_type = 'ClusterIP'

        self.service = k8s.core.v1.Service(
            resource_name=f'{resource_name}:service',
            metadata=k8s.meta.v1.ObjectMetaArgs(
                name='deluge',
                namespace=namespace,
            ),
            spec=k8s.core.v1.ServiceSpecArgs(
                selector={
                    'app': 'deluge',
                },
                ports=[
                    http_port,
                    k8s.core.v1.ServicePortArgs(name='torrent-tcp', port=6881, protocol='TCP'),
                    k8s.core.v1.ServicePortArgs(name='torrent-udp', port=6881, protocol='UDP'),
                ],
                type=svc_type,
            ),
            opts=pulumi.ResourceOptions(
                parent=self,
                depends_on=[self.deploy],
            ),
        )
