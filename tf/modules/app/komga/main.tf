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
  host = "komga.${var.domain}"
}

resource "kubernetes_persistent_volume_claim" "komga" {
  metadata {
    name = "komga"
    namespace = local.namespace
  }
  spec {
    access_modes = ["ReadWriteOnce"]
    resources {
      requests = {
        storage = "50Mi"
      }
    }
  }
}

resource "kubernetes_deployment" "komga" {
  metadata {
    name = "komga"
    namespace = local.namespace
  }
  spec {
    selector {
      match_labels = {
        app = "komga"
      }
    }
    template {
      metadata {
        labels = {
          app = "komga"
        }
      }
      spec {
        container {
          name = "main"
          image = "gotson/komga:0.99.2"
          env {
            name = "KOMGA_DELETE_EMPTY_COLLECTIONS"
            value = "false"
          }
          volume_mount {
            name = "media"
            mount_path = "/media"
          }
          volume_mount {
            name = "komga"
            mount_path = "/config"
          }
          security_context {
            run_as_user = 1000
            run_as_group = 1000
          }
          resources {
            limits = {
              # Komga seems to have a leak? Pls don't crash my server
              # Holy hell it's hungry for memory. Currently exponentially searching what makes this happy
              memory = "2Gi"
            }
          }
        }
        volume {
          name = "media"
          persistent_volume_claim {
            claim_name = var.media-pvc
          }
        }
        volume {
          name = "komga"
          persistent_volume_claim {
            claim_name = kubernetes_persistent_volume_claim.komga.metadata[0].name
          }
        }
      }
    }
  }
}

resource "kubernetes_service" "komga" {
  metadata {
    name = "komga"
    namespace = local.namespace
  }
  spec {
    selector = {
      app = "komga"
    }
    port {
      port = 8080
      name = "http"
    }
  }
}

module "protected_ingress" {
  source = "../../../modules/app_infra/authproxy/protected_ingress"
  authproxy_host = var.authproxy_host
  name = "komga"
  namespace = local.namespace
  host = local.host
  service_name = kubernetes_service.komga.metadata[0].name
  service_port = "http"
  tls_secret = var.tls_secret
}

output "host" {
  value = local.host
}