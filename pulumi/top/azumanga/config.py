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
    deluge = 12001
    pydio = 12002
    photoprism = 12003
    filebrowser = 12004
