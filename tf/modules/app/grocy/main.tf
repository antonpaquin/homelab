variable "domain" {
  type = string
}

variable "authproxy_host" {
  type = string
  description = "Authproxy host (for protected ingress)"
}

variable "tls_secret" {
  type = string
  description = "Name of secret where the TLS certificate is located"
}

locals {
  namespace = "default"
  host = "grocy.${var.domain}"

  // See https://github.com/grocy/grocy/blob/master/config-dist.php
  grocy_conf = {
    "config-dist.php": file("${path.module}/config-dist.php")
  }
}

resource "kubernetes_config_map" "grocy" {
  metadata {
    name = "grocy-conf"
    namespace = local.namespace
  }
  data = local.grocy_conf
}

resource "kubernetes_persistent_volume_claim" "grocy" {
  metadata {
    name = "grocy"
    namespace = local.namespace
  }
  spec {
    access_modes = ["ReadWriteOnce"]
    resources {
      requests = {
        storage = "10Gi"
      }
    }
  }
}

resource "kubernetes_deployment" "grocy" {
  wait_for_rollout = false
  metadata {
    name = "grocy"
    namespace = local.namespace
  }
  spec {
    selector {
      match_labels = {
        app = "grocy"
      }
    }
    template {
      metadata {
        labels = {
          app = "grocy"
        }
      }
      spec {
        container {
          name = "main"
          image = "lscr.io/linuxserver/grocy"
          volume_mount {
            name = "grocy"
            mount_path = "/config"
          }
          volume_mount {
            name = "config"
            mount_path = "/config/data/config.php"
            sub_path = "config-dist.php"
          }
        }
        volume {
          name = "grocy"
          persistent_volume_claim {
            claim_name = kubernetes_persistent_volume_claim.grocy.metadata[0].name
          }
        }
        volume {
          name = "config"
          config_map {
            name = kubernetes_config_map.grocy.metadata[0].name
          }
        }
      }
    }
  }
}

resource "kubernetes_service" "grocy" {
  metadata {
    name = "grocy"
    namespace = local.namespace
  }
  spec {
    selector = {
      app = "grocy"
    }
    port {
      port = 80
      name = "http"
    }
  }
}

module "protected_ingress" {
  source = "../../../modules/app_infra/authproxy/protected_ingress"
  host = local.host
  authproxy_host = var.authproxy_host
  name = "grocy"
  namespace = local.namespace
  service_name = kubernetes_service.grocy.metadata[0].name
  service_port = "http"
  extra_annotations = {
    "nginx.ingress.kubernetes.io/proxy-send-timeout": 3600
    "nginx.ingress.kubernetes.io/proxy-read-timeout": 3600
    "nginx.ingress.kubernetes.io/proxy-body-size": "8192m"
    "nginx.ingress.kubernetes.io/configuration-snippet": join("\n", [
      "auth_request_set $auth_resp_user $upstream_http_x_authproxy_user;",
      "proxy_set_header X-User $auth_resp_user;"
    ])
  }
  tls_secret = var.tls_secret
}

output "host" {
  value = local.host
}