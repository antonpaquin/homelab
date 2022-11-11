variable "domain" {
  type = string
}

variable "authproxy_host" {
  type = string
  description = "Authproxy host (for protected ingress)"
}

variable "media-pvc" {
  type = string
}

variable "tls_secret" {
  type = string
  description = "Secret containing a wildcard certificate of the type kubernetes.io/tls"
}

locals {
  namespace = "default"
  host = "metube.${var.domain}"
}

resource "kubernetes_deployment" "metube" {
  metadata {
    name = "metube"
    namespace = local.namespace
  }
  spec {
    selector {
      match_labels = {
        app = "metube"
      }
    }
    template {
      metadata {
        labels = {
          app = "metube"
        }
      }
      spec {
        container {
          name = "main"
          image = "docker.io/alexta69/metube:2022-02-18"  # Metube not so good at pinning non-"latest", until recently?
          env {
            name = "DOWNLOAD_DIR"
            value = "/media/ingest/metube"
          }
          env {
            name = "STATE_DIR"
            value = "/media/ingest/metube/.state"
          }
          volume_mount {
            name = "media"
            mount_path = "/media"
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
      }
    }
  }
}

resource "kubernetes_service" "metube" {
  metadata {
    name = "metube"
    namespace = local.namespace
  }
  spec {
    selector = {
      app = "metube"
    }
    port {
      port = 8081
      name = "http"
    }
  }
}

module "protected_ingress" {
  source = "../../../modules/app_infra/authproxy/protected_ingress"
  host = local.host
  authproxy_host = var.authproxy_host
  namespace = local.namespace
  name = "metube"
  service_name = "metube"
  service_port = "http"
  tls_secret = var.tls_secret
}

output "host" {
  value = local.host
}