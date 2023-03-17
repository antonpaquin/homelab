from modules.lib.config_types import ClusterNode

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


class Ports:
    # Default: sakaki is exposed 12001-12100
    # (May change when I cycle routers)
    deluge = 12001
    pydio = 12002
    photoprism = 12003
    filebrowser = 12004
    heimdall = 12005
    plex = 12006
    metube = 12007
    calibre = 12008
    overseerr = 12009
