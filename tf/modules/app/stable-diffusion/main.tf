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
  host = "stable-diffusion.${var.domain}"
}

resource "kubernetes_persistent_volume_claim" "stable-diffusion" {
  metadata {
    name = "stable-diffusion-models"
    namespace = local.namespace
  }
  spec {
    access_modes = ["ReadWriteMany"]
    storage_class_name = "ceph-cephfs"
    resources {
      requests = {
        storage = "80Gi"
      }
    }
  }
}

resource "kubernetes_deployment" "stable-diffusion" {
  metadata {
    name = "stable-diffusion"
    namespace = local.namespace
  }
  spec {
    selector {
      match_labels = {
        app = "stable-diffusion"
      }
    }
    template {
      metadata {
        labels = {
          app = "stable-diffusion"
        }
      }
      spec {
        container {
          name = "main"
          image = "antonpaquin/misc:stable-diffusion-webui"
          volume_mount {
            name = "models"
            mount_path = "/models"
          }
          resources {
            requests = {
              "nvidia.com/gpu" = "1"
            }
            limits = {
              "nvidia.com/gpu" = "1"
            }
          }
        }
        toleration {
          key = "nvidia.com/gpu"
          operator = "Equal"
          value = "true"
        }
        volume {
          name = "models"
          persistent_volume_claim {
            claim_name = kubernetes_persistent_volume_claim.stable-diffusion.metadata[0].name
          }
        }
      }
    }
  }
}

resource "kubernetes_service" "stable-diffusion" {
  metadata {
    name = "stable-diffusion"
    namespace = local.namespace
  }
  spec {
    selector = {
      app = "stable-diffusion"
    }
    port {
      port = 7860
      name = "http"
    }
  }
}

module "protected_ingress" {
  source = "../../modules/authproxy/protected_ingress"
  host = local.host
  authproxy_host = var.authproxy_host
  namespace = local.namespace
  name = "stable-diffusion"
  service_name = kubernetes_service.stable-diffusion.metadata[0].name
  service_port = "http"
  tls_secret = var.tls_secret
}

output "host" {
  value = local.host
}