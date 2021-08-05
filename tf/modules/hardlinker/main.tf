variable "domain" {
  type = string
  default = "k8s.local"
}

variable "media-pvc" {
  type = string
}

locals {
  namespace = "default"
  host = "hardlinker.${var.domain}"
}

resource "kubernetes_persistent_volume_claim" "hardlinker" {
  metadata {
    name = "hardlinker"
    namespace = local.namespace
  }
  spec {
    access_modes = ["ReadWriteOnce"]
    resources {
      requests = {
        storage = "80Mi"
      }
    }
  }
}

resource "kubernetes_deployment" "hardlinker" {
  metadata {
    name = "hardlinker"
    namespace = local.namespace
  }
  spec {
    selector {
      match_labels = {
        app = "hardlinker"
      }
    }
    template {
      metadata {
        labels = {
          app = "hardlinker"
        }
      }
      spec {
        container {
          name = "main"
          image = "antonpaquin/misc:hardlinker"
          image_pull_policy = "Always"
          env {
            name = "LISTEN_ROOT"
            value = "/media/torrents/complete"
          }
          env {
            name = "DB_PATH"
            value = "/var/hardlinker/data/db.sqlite"
          }
          env {
            name = "APP_HOST"
            value = "0.0.0.0"
          }
          env {
            name = "APP_PORT"
            value = "4000"
          }
          volume_mount {
            name = "media"
            mount_path = "/media"
          }
          volume_mount {
            name = "hardlinker"
            mount_path = "/var/hardlinker/data"
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
          name = "hardlinker"
          persistent_volume_claim {
            claim_name = kubernetes_persistent_volume_claim.hardlinker.metadata[0].name
          }
        }
      }
    }
  }
}

resource "kubernetes_service" "hardlinker" {
  metadata {
    name = "hardlinker"
    namespace = local.namespace
  }
  spec {
    selector = {
      app = "hardlinker"
    }
    port {
      port = 4000
      name = "http"
    }
  }
}

resource "kubernetes_ingress" "hardlinker" {
  metadata {
    name = "hardlinker"
    namespace = local.namespace
  }
  spec {
    rule {
      host = local.host
      http {
        path {
          path = "/"
          backend {
            service_name = kubernetes_service.hardlinker.metadata[0].name
            service_port = "http"
          }
        }
      }
    }
  }
}

output "host" {
  value = local.host
}