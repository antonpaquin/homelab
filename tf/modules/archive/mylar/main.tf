variable "domain" {
  type = string
  default = "k8s.local"
}

variable "media-pvc" {
  type = string
}

locals {
  namespace = "default"
}

resource "kubernetes_persistent_volume_claim" "mylar" {
  metadata {
    name = "mylar"
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

resource "kubernetes_deployment" "mylar" {
  metadata {
    name = "mylar"
    namespace = local.namespace
  }
  spec {
    selector {
      match_labels = {
        app = "mylar"
      }
    }
    template {
      metadata {
        labels = {
          app = "mylar"
        }
      }
      spec {
        container {
          name = "main"
          image = "linuxserver/mylar3:version-v0.5.3"
          env {
            name = "PUID"
            value = "1000"
          }
          env {
            name = "PGID"
            value = "1000"
          }
          volume_mount {
            name = "media"
            mount_path = "/media"
          }
          volume_mount {
            name = "mylar"
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
          name = "mylar"
          persistent_volume_claim {
            claim_name = kubernetes_persistent_volume_claim.mylar.metadata[0].name
          }
        }
      }
    }
  }
}

resource "kubernetes_service" "mylar" {
  metadata {
    name = "mylar"
    namespace = local.namespace
  }
  spec {
    selector = {
      app = "mylar"
    }
    port {
      port = 8090
      name = "http"
    }
  }
}

resource "kubernetes_ingress" "mylar" {
  metadata {
    name = "mylar"
    namespace = local.namespace
  }
  spec {
    rule {
      host = "mylar.${var.domain}"
      http {
        path {
          path = "/"
          backend {
            service_name = kubernetes_service.mylar.metadata[0].name
            service_port = "http"
          }
        }
      }
    }
  }
}