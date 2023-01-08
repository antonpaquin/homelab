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

variable "huggingface_cache_pv_name" {
  type = string
}

locals {
  namespace = "default"
  host = "distributed-diffusion.${var.domain}"
}

resource "kubernetes_persistent_volume_claim" "distributed-diffusion" {
  metadata {
    name = "distributed-diffusion-workspace"
    namespace = local.namespace
  }
  spec {
    access_modes = ["ReadWriteMany"]
    storage_class_name = "nfs-client"
    resources {
      requests = {
        storage = "80Gi"
      }
    }
  }
}


resource "kubernetes_deployment" "distributed-diffusion" {
  wait_for_rollout = false
  metadata {
    name = "distributed-diffusion"
    namespace = local.namespace
  }
  spec {
    selector {
      match_labels = {
        app = "distributed-diffusion"
      }
    }
    template {
      metadata {
        labels = {
          app = "distributed-diffusion"
        }
      }
      spec {
        container {
          name = "main"
          image = "ghcr.io/chavinlo/distributed-diffusion:sha-6bf010a"
          resources {
            requests = {
              "nvidia.com/gpu" = "1"
            }
            limits = {
              "nvidia.com/gpu" = "1"
            }
          }
          volume_mount {
            name = "huggingface"
            mount_path = "/root/.cache/huggingface"
          }
        }
        toleration {
          key = "nvidia.com/gpu"
          operator = "Equal"
          value = "true"
        }
        volume {
          name = "huggingface"
          persistent_volume_claim {
            claim_name = var.huggingface_cache_pv_name
          }
        }
      }
    }
  }
}

resource "kubernetes_service" "distributed-diffusion" {
  metadata {
    name = "distributed-diffusion"
    namespace = local.namespace
  }
  spec {
    selector = {
      app = "distributed-diffusion"
    }
    port {
      port = 5080
      name = "http"
    }
  }
}

module "protected_ingress" {
  source = "../../../modules/app_infra/authproxy/protected_ingress"
  host = local.host
  authproxy_host = var.authproxy_host
  namespace = local.namespace
  name = "distributed-diffusion"
  service_name = kubernetes_service.distributed-diffusion.metadata[0].name
  service_port = "http"
  tls_secret = var.tls_secret
  extra_annotations = {
    "nginx.ingress.kubernetes.io/proxy-send-timeout": 3600
    "nginx.ingress.kubernetes.io/proxy-read-timeout": 3600
    "nginx.ingress.kubernetes.io/proxy-body-size": "8192m"
  }
}

output "host" {
  value = local.host
}