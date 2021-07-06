variable "domain" {
  type = string
  default = "k8s.local"
}

variable "media-pvc" {
  type = string
}

locals {
  namespace = "default"
  host = "TEMPLATE.${var.domain}"
}

resource "kubernetes_config_map" "TEMPLATE" {
  metadata {
    name = "TEMPLATE"
    namespace = local.namespace
  }
  data = {
  }
}

resource "kubernetes_persistent_volume_claim" "TEMPLATE" {
  metadata {
    name = "TEMPLATE"
    namespace = local.namespace
  }
  spec {
    access_modes = ["ReadWriteOnce"]
    resources {
      requests = {
        storage = "TODO"
      }
    }
  }
}

resource "kubernetes_deployment" "TEMPLATE" {
  metadata {
    name = "TEMPLATE"
    namespace = local.namespace
  }
  spec {
    selector {
      match_labels = {
        app = "TEMPLATE"
      }
    }
    template {
      metadata {
        labels = {
          app = "TEMPLATE"
        }
      }
      spec {
        container {
          name = "main"
          image = "TODO"
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
            name = "TEMPLATE"
            mount_path = "TODO"
          }
          volume_mount {
            name = "config"
            mount_path = "TODO"
          }
        }
        volume {
          name = "media"
          persistent_volume_claim {
            claim_name = var.media-pvc
          }
        }
        volume {
          name = "TEMPLATE"
          persistent_volume_claim {
            claim_name = kubernetes_persistent_volume_claim.TEMPLATE.metadata[0].name
          }
        }
        volume {
          name = "config"
          config_map {
            name = kubernetes_config_map.TEMPLATE.metadata[0].name
          }
        }
      }
    }
  }
}

resource "kubernetes_service" "TEMPLATE" {
  metadata {
    name = "TEMPLATE"
    namespace = local.namespace
  }
  spec {
    selector = {
      app = "TEMPLATE"
    }
    port {
      port = TODO
      name = "http"
    }
  }
}

resource "kubernetes_ingress" "TEMPLATE" {
  metadata {
    name = "TEMPLATE"
    namespace = local.namespace
  }
  spec {
    rule {
      host = local.host
      http {
        path {
          path = "/"
          backend {
            service_name = kubernetes_service.TEMPLATE.metadata[0].name
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