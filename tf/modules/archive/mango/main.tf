variable "media-pvc" {
  type = string
}

variable "domain" {
  type = string
  default = "k8s.local"
}

locals {
  namespace = "default"
}

resource "kubernetes_persistent_volume_claim" "mango" {
  metadata {
    name = "mango"
    namespace = local.namespace
  }
  spec {
    access_modes = ["ReadWriteOnce"]
    resources {
      requests = {
        storage = "100Mi"
      }
    }
  }
}

resource "kubernetes_config_map" "mango" {
  metadata {
    name = "mango"
    namespace = local.namespace
  }
  data = {
    "config.yml" = <<EOF
host: 0.0.0.0
port: 9000
base_url: /
session_secret: mango-session-secret
library_path: /media/library/manga
db_path: /mango/mango.db
scan_interval_minutes: 120
thumbnail_generation_interval_hours: 24
log_level: info
upload_path: /mango/uploads
plugin_path: /mango/plugins
download_timeout_seconds: 30
page_margin: 30
disable_login: false
default_username: ""
auth_proxy_header_name: ""
mangadex:
  base_url: https://mangadex.org
  api_url: https://api.mangadex.org/v2
  download_wait_seconds: 5
  download_retries: 4
  download_queue_db_path: /mango/queue.db
  chapter_rename_rule: 'c{chapter}-{title|id}'
  manga_rename_rule: '{title}'
EOF
  }
}

resource "kubernetes_deployment" "mango" {
  metadata {
    name = "mango"
    namespace = local.namespace
  }
  spec {
    selector {
      match_labels = {
        app = "mango"
      }
    }
    template {
      metadata {
        name = "mango"
        labels = {
          app = "mango"
        }
      }
      spec {
        container {
          name = "main"
          image = "hkalexling/mango:v0.21.0"
          volume_mount {
            name = "media"
            mount_path = "/media"
          }
          volume_mount {
            name = "mango"
            mount_path = "/mango"
          }
          volume_mount {
            name = "config"
            mount_path = "/root/.config/mango"
          }
        }
        volume {
          name = "media"
          persistent_volume_claim {
            claim_name = var.media-pvc
          }
        }
        volume {
          name = "mango"
          persistent_volume_claim {
            claim_name = kubernetes_persistent_volume_claim.mango.metadata[0].name
          }
        }
        volume {
          name = "config"
          config_map {
            name = kubernetes_config_map.mango.metadata[0].name
          }
        }
      }
    }
  }
}

resource "kubernetes_service" "mango" {
  metadata {
    name = "mango"
    namespace = local.namespace
  }
  spec {
    selector = {
      app = "mango"
    }
    port {
      name = "http"
      port = 9000
    }
  }
}

resource "kubernetes_ingress_v1" "mango" {
  metadata {
    name = "mango"
    namespace = local.namespace
  }
  spec {
    rule {
      host = "mango.${var.domain}"
      http {
        path {
          path = "/"
          backend {
            service_name = kubernetes_service.mango.metadata[0].name
            service_port = "http"
          }
        }
      }
    }
  }
}

