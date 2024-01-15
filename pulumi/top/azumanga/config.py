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
    calibre_web = 12010
    kavita = 12011
    vaultwarden = 12012
    readarr = 12013
    sonarr = 12014
    jellyfin = 12015
    sabnzbd = 12016
    radarr = 12017

    homepage = 12020

    omada_controller = 8043
    # Also uses 8088, 8843, 27001, 29810-29814


# Calibre is kinda crazy so I'm turning it off for now
# ... does it really give us much over kavita alone, if we're DIYing /books?