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
  description = "Secret containing a wildcard certificate of the type kubernetes.io/tls"
}

locals {
  namespace = "default"
  host = "jellyfin.${var.domain}"
}

resource "kubernetes_persistent_volume_claim" "jellyfin" {
  metadata {
    name = "jellyfin"
    namespace = local.namespace
  }
  spec {
    access_modes = ["ReadWriteOnce"]
    resources {
      requests = {
        storage = "50Gi"
      }
    }
  }
}

resource "kubernetes_deployment" "jellyfin" {
  wait_for_rollout = false
  metadata {
    name = "jellyfin"
    namespace = local.namespace
  }
  spec {
    selector {
      match_labels = {
        app = "jellyfin"
      }
    }
    template {
      metadata {
        labels = {
          app = "jellyfin"
        }
      }
      spec {
        container {
          name = "main"
          # Jellyfin having playback issues... tries to use all cores and then dies, or is very laggy, etc
          # maybe version bump helps?
          # image = "docker.io/jellyfin/jellyfin:10.8.9"
          image = "docker.io/jellyfin/jellyfin:10.7.6"
          volume_mount {
            name = "media"
            mount_path = "/media"
          }
          volume_mount {
            name = "jellyfin"
            mount_path = "/config"
          }
          resources {
            # jellyfin likes to burst to 100Gi for some reason?
            # please stop crashing the server when trying to play video
            requests = {
              "memory" = "5Gi"
            }
            limits = {
              "memory" = "10Gi"
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
          name = "jellyfin"
          persistent_volume_claim {
            claim_name = kubernetes_persistent_volume_claim.jellyfin.metadata[0].name
          }
        }
      }
    }
  }
}

resource "kubernetes_service" "jellyfin" {
  metadata {
    name = "jellyfin"
    namespace = local.namespace
  }
  spec {
    selector = {
      app = "jellyfin"
    }
    port {
      port = 80
      name = "http"
      target_port = 8096
    }
  }
}

# module "protected_ingress" {
#   source = "../../../modules/app_infra/authproxy/protected_ingress"
#   host = local.host
#   authproxy_host = var.authproxy_host
#   name = "jellyfin"
#   namespace = local.namespace
#   service_name = kubernetes_service.jellyfin.metadata[0].name
#   service_port = "http"
#   tls_secret = var.tls_secret
# }

resource "kubernetes_ingress_v1" "jellyfin" {
  metadata {
    name = "jellyfin"
    namespace = local.namespace
  }
  spec {
    ingress_class_name = "nginx"
    rule {
      host = local.host
      http {
        path {
          path = "/"
          backend {
            service {
              name = kubernetes_service.jellyfin.metadata[0].name
              port {
                name = "http"
              }
            }
          }
        }
      }
    }
  }
}

output "host" {
  value = local.host
}