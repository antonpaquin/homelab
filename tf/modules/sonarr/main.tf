variable "domain" {
  type = string
  default = "k8s.local"
}

variable "media-pvc" {
  type = string
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
          image = "linuxserver/sonarr:version-3.0.6.1196"
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

resource "kubernetes_ingress" "sonarr" {
  metadata {
    name = "sonarr"
    namespace = local.namespace
  }
  spec {
    rule {
      host = local.host
      http {
        path {
          path = "/"
          backend {
            service_name = kubernetes_service.sonarr.metadata[0].name
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