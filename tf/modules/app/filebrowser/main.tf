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
  host = "filebrowser.${var.domain}"
}

resource "kubernetes_config_map" "filebrowser" {
  metadata {
    name = "filebrowser"
    namespace = local.namespace
  }
  data = {
    "filebrowser.json" = <<EOF
{
  "port": 80,
  "baseURL": "",
  "address": "",
  "log": "stdout",
  "database": "/tmp/filebrowser.db",
  "root": "/srv"
}
EOF
    "entrypoint.sh" = <<EOF
#! /bin/sh

set -e

# NB: the config json is just CLI params, "config set" is separate
# There must be a user, but with method=noauth it's just a dummy

/filebrowser -c /etc/filebrowser/filebrowser.json config init
/filebrowser -c /etc/filebrowser/filebrowser.json config set --auth.method=noauth
/filebrowser -c /etc/filebrowser/filebrowser.json users add nouser nopass
/filebrowser -c /etc/filebrowser/filebrowser.json
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
          image = "docker.io/filebrowser/filebrowser:v2.15.0"
          command = ["/etc/filebrowser/entrypoint.sh"]
          volume_mount {
            name = "media"
            mount_path = "/srv/media"
          }
          volume_mount {
            name = "config"
            mount_path = "/etc/filebrowser"
          }
          security_context {
            run_as_user = 1000
            run_as_group = 1000
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
              key = "filebrowser.json"
              path = "filebrowser.json"
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

module "protected_ingress" {
  source = "../../../modules/app_infra/authproxy/protected_ingress"
  host = local.host
  authproxy_host = var.authproxy_host
  name = "filebrowser"
  namespace = local.namespace
  service_name = kubernetes_service.filebrowser.metadata[0].name
  service_port = "http"
  extra_annotations = {
    "nginx.ingress.kubernetes.io/proxy-send-timeout": 3600
    "nginx.ingress.kubernetes.io/proxy-read-timeout": 3600
    "nginx.ingress.kubernetes.io/proxy-body-size": "8192m"

    # "nginx.ingress.kubernetes.io/configuration-snippet": "client_max_body_size 5tb;"

  }
  tls_secret = var.tls_secret
}

output "host" {
  value = local.host
}
