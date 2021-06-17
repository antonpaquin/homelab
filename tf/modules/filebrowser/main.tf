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

resource "kubernetes_config_map" "filebrowser" {
  metadata {
    name = "filebrowser"
    namespace = local.namespace
  }
  data = {
    ".filebrowser.json" = <<EOF
{
  "port": 80,
  "baseURL": "",
  "address": "",
  "log": "stdout",
  "database": "/file/browser/database.db",
  "root": "/srv"
}
EOF
    "entrypoint.sh" = <<EOF
#! /bin/sh

cp /etc/filebrowser/.filebrowser.json /.filebrowser.json

/filebrowser config init
/filebrowser config set --auth.method=noauth
/filebrowser users add admin cirno9ball

/filebrowser
EOF
  }
}

resource "kubernetes_deployment" "filebrowser" {
  metadata {
    name = "filebrowser"
    namespace = local.namespace
  }
  spec {
    selector {
      match_labels = {
        app = "filebrowser"
      }
    }
    template {
      metadata {
        labels = {
          app = "filebrowser"
        }
      }
      spec {
        container {
          name = "main"
          image = "filebrowser/filebrowser:v2.15.0"
          command = ["/etc/filebrowser/entrypoint.sh"]
          volume_mount {
            name = "media"
            mount_path = "/srv/media"
          }
          volume_mount {
            name = "config"
            mount_path = "/etc/filebrowser"
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
          config_map {
            name = kubernetes_config_map.filebrowser.metadata[0].name
            items {
              key = "entrypoint.sh"
              path = "entrypoint.sh"
              mode = "0777"
            }
            items {
              key = ".filebrowser.json"
              path = ".filebrowser.json"
            }
          }
        }
      }
    }
  }
}

resource "kubernetes_service" "filebrowser" {
  metadata {
    name = "filebrowser"
    namespace = local.namespace
  }
  spec {
    selector = {
      app = "filebrowser"
    }
    port {
      port = 80
      target_port = 80
      name = "http"
    }
  }
}

resource "kubernetes_ingress" "filebrowser" {
  metadata {
    name = "filebrowser"
    namespace = local.namespace
  }
  spec {
    rule {
      host = "filebrowser.${var.domain}"
      http {
        path {
          path = "/"
          backend {
            service_name = kubernetes_service.filebrowser.metadata[0].name
            service_port = "http"
          }
        }
      }
    }
  }
}
