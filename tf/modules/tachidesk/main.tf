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

resource "kubernetes_deployment" "tachidesk" {
  metadata {
    name = "tachidesk"
    namespace = local.namespace
  }
  spec {
    selector {
      match_labels = {
        app = "tachidesk"
      }
    }
    template {
      metadata {
        labels = {
          app = "tachidesk"
        }
      }
      spec {
        container {
          name = "tachidesk"
          image = "ghcr.io/suwayomi/tachidesk"
          env {
            name = "TZ"
            value = "US/Pacific"
          }
          volume_mount {
            mount_path = "/media"
            name = "media"
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

resource "kubernetes_service" "tachidesk" {
  metadata {
    name = "tachidesk"
    namespace = local.namespace
  }
  spec {
    selector = {
      app = "tachidesk"
    }
    port {
      name = "tachidesk"
      port = 4567
    }
  }
}

resource "kubernetes_ingress" "tachidesk" {
  metadata {
    name = "tachidesk"
    namespace = local.namespace
  }
  spec {
    rule {
      host = "tachidesk.${var.domain}"
      http {
        path {
          path = "/"
          backend {
            service_name = kubernetes_service.tachidesk.metadata[0].name
            service_port = "tachidesk"
          }
        }
      }
    }
  }
}

