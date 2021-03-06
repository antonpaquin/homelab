variable "domain" {
  type = string
}

locals {
  namespace = "default"
  host = "devpi.${var.domain}"
}

resource "kubernetes_persistent_volume_claim" "devpi" {
  metadata {
    name = "devpi"
    namespace = local.namespace
  }
  spec {
    access_modes = ["ReadWriteOnce"]
    resources {
      requests = {
        storage = "20Gi"
      }
    }
  }
}

resource "kubernetes_deployment" "devpi" {
  metadata {
    name = "devpi"
    namespace = local.namespace
  }
  spec {
    selector {
      match_labels = {
        app = "devpi"
      }
    }
    template {
      metadata {
        labels = {
          app = "devpi"
        }
      }
      spec {
        container {
          name = "main"
          image = "thomasf/devpi:5.5.1-1"
          env {
            name = "DEVPISERVER_OUTSIDE_URL"
            value = "http://${local.host}"
          }
          env {
            name = "DEVPISERVER_SERVERDIR"
            value = "/devpi/data"
          }
          volume_mount {
            name = "devpi"
            mount_path = "/devpi/data"
          }
        }
        volume {
          name = "devpi"
          persistent_volume_claim {
            claim_name = kubernetes_persistent_volume_claim.devpi.metadata[0].name
          }
        }
      }
    }
  }
}

resource "kubernetes_service" "devpi" {
  metadata {
    name = "devpi"
    namespace = local.namespace
  }
  spec {
    selector = {
      app = "devpi"
    }
    port {
      port = 3141
      name = "http"
    }
  }
}

resource "kubernetes_ingress" "devpi" {
  metadata {
    name = "devpi"
    namespace = local.namespace
  }
  spec {
    rule {
      host = local.host
      http {
        path {
          path = "/"
          backend {
            service_name = kubernetes_service.devpi.metadata[0].name
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