variable "domain" {
  type = string
  default = "k8s.local"
}

variable "media-pvc" {
  type = string
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
          image = "alexta69/metube"
          env {
            name = "DOWNLOAD_DIR"
            value = "/media/ingest/metube"
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
  source = "../../modules/authproxy/protected_ingress"
  host = local.host
  namespace = local.namespace
  name = "metube"
  service_name = "metube"
  service_port = "http"
}

output "host" {
  value = local.host
}