variable "domain" {
  type = string
}

variable "media-pvc" {
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
  host = "sonarr.${var.domain}"
}

resource "kubernetes_persistent_volume_claim" "sonarr" {
  metadata {
    name = "sonarr"
    namespace = local.namespace
  }
  spec {
    access_modes = ["ReadWriteOnce"]
    resources {
      requests = {
        storage = "30Mi"
      }
    }
  }
}

resource "kubernetes_deployment" "sonarr" {
  wait_for_rollout = false
  metadata {
    name = "sonarr"
    namespace = local.namespace
  }
  spec {
    selector {
      match_labels = {
        app = "sonarr"
      }
    }
    template {
      metadata {
        labels = {
          app = "sonarr"
        }
      }
      spec {
        container {
          name = "main"
          image = "docker.io/linuxserver/sonarr:version-3.0.6.1196"
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
            name = "media"
            mount_path = "/media"  # Should match "deluge"
          }
          volume_mount {
            name = "config"
            mount_path = "/config"
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
            claim_name = kubernetes_persistent_volume_claim.sonarr.metadata[0].name
          }
        }
      }
    }
  }
}

resource "kubernetes_service" "sonarr" {
  metadata {
    name = "sonarr"
    namespace = local.namespace
  }
  spec {
    selector = {
      app = "sonarr"
    }
    port {
      name = "http"
      port = 8989
    }
  }
}

module "protected_ingress" {
  source = "../../../modules/app_infra/authproxy/protected_ingress"
  host = local.host
  authproxy_host = var.authproxy_host
  namespace = local.namespace
  name = "sonarr"
  service_name = "sonarr"
  service_port = "http"
  tls_secret = var.tls_secret
}

output "host" {
  value = local.host
}