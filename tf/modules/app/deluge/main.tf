variable "media-pvc" {
  type = string
}

variable "domain" {
  type = string
}

variable "authproxy_host" {
  type = string
  description = "Authproxy host (for protected ingress)"
}

variable "tls_secret" {
  type = string
  description = "Secret containing a wildcard certificate of the type kubernetes.io/tls"
}

locals {
  namespace = "default"
  auth = {
    username: "reimu"
    password: "cirno9ball"  # insecure?
  }
  host = "deluge.${var.domain}"
}

locals {
  max_upload_speed = "5"  # kb/s
  max_download_speed = "80"  # kb/s
}

resource "kubernetes_persistent_volume_claim" "deluge-config" {
  lifecycle {prevent_destroy = true}
  metadata {
    name = "deluge-config"
    namespace = local.namespace
  }
  spec {
    access_modes = ["ReadWriteOnce"]
    resources {
      requests = {
        storage = "20Mi"
      }
    }
  }
}

resource "kubernetes_config_map" "deluge-config" {
  metadata {
    name = "deluge-config"
    namespace = local.namespace
  }
  data = {
    "core.conf": <<EOF
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
    "download_location": "/media/torrents/progress",
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
    "max_download_speed": ${local.max_download_speed},
    "max_download_speed_per_torrent": -1,
    "max_half_open_connections": 50,
    "max_upload_slots_global": 4,
    "max_upload_slots_per_torrent": -1,
    "max_upload_speed": ${local.max_upload_speed},
    "max_upload_speed_per_torrent": -1,
    "move_completed": true,
    "move_completed_path": "/media/torrents/complete",
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
    "torrentfiles_location": "/media/torrents/torrentfiles",
    "upnp": true,
    "utpex": true
}
EOF
    auth: <<EOF
localclient:cf1bf6ad72a65a6cc7dd053ee0643007d56a392b:10
${local.auth["username"]}:${local.auth["password"]}:10
EOF
    "web.conf": <<EOF
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
    "pwd_salt": "ee41e8fd8504c493ed4825491e86b7b27acf5ec1",
    "pwd_sha1": "05b545d4fc9f031e0e20dca40f5bc03becbb697a",
    "session_timeout": 3600,
    "sessions": {
        "47e6db9cc55e7298ce9062fd0fce4bf2b672af91ee4b0ff3d6d5863d5b2e4cdf": {
            "expires": 1623644703.0,
            "level": 10,
            "login": "admin"
        }
    },
    "show_session_speed": false,
    "show_sidebar": true,
    "sidebar_multiple_filters": true,
    "sidebar_show_zero": false,
    "theme": "gray"
}
EOF
  }
}

resource "kubernetes_deployment" "deluge" {
  metadata {
    name = "deluge"
    namespace = local.namespace
  }
  spec {
    selector {
      match_labels = {
        app = "deluge"
      }
    }
    template {
      metadata {
        labels = {
          app = "deluge"
        }
      }
      spec {
        container {
          name = "main"
          image = "ghcr.io/linuxserver/deluge"
          env {
            name = "PUID"
            value = "1000"
          }
          env {
            name = "PGID"
            value = "1000"
          }
          env {
            name = "TZ"
            value = "US/Pacific"
          }
          volume_mount {
            mount_path = "/media"
            name = "media"
          }
          volume_mount {
            mount_path = "/config"
            name = "config"
          }
          volume_mount {
            mount_path = "/config/core.conf"
            name = "config-file"
            sub_path = "core.conf"
          }
          volume_mount {
            mount_path = "/config/auth"
            name = "config-file"
            sub_path = "auth"
          }
          volume_mount {
            mount_path = "/config/web.conf"
            name = "config-file"
            sub_path = "web.conf"
          }
        }
        volume {
          name = "media"
          persistent_volume_claim {
            claim_name = var.media-pvc
          }
        }
        volume {
          name = "config"
          persistent_volume_claim {
            claim_name = kubernetes_persistent_volume_claim.deluge-config.metadata[0].name
          }
        }
        volume {
          name = "config-file"
          config_map {
            name = kubernetes_config_map.deluge-config.metadata[0].name
          }
        }
      }
    }
  }
}

resource "kubernetes_service" "deluge" {
  metadata {
    name = "deluge"
    namespace = local.namespace
  }
  spec {
    selector = {
      app = "deluge"
    }
    port {
      name = "http"
      port = 8112
    }
    port {
      name = "torrent-tcp"
      port = 6881
      protocol = "TCP"
    }
    port {
      name = "torrent-udp"
      port = 6881
      protocol = "UDP"
    }
  }
}

module "protected_ingress" {
  source = "../../../modules/app_infra/authproxy/protected_ingress"
  host = local.host
  authproxy_host = var.authproxy_host
  name = "deluge"
  namespace = local.namespace
  service_name = kubernetes_service.deluge.metadata[0].name
  service_port = "http"
  tls_secret = var.tls_secret
}


resource "kubernetes_ingress" "deluge-api" {
  # Un-SSO'd version (still uses password auth) for "Torrent Control" browser extension reasons
  metadata {
    name = "deluge-api"
    namespace = local.namespace
  }
  spec {
    rule {
      host = "api.${local.host}"
      http {
        path {
          path = "/"
          backend {
            service_name = kubernetes_service.deluge.metadata[0].name
            service_port = "http"
          }
        }
      }
    }
  }
}

output "host" {
  value = local.host
}
