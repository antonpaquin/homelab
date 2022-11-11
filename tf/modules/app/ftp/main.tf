variable "domain" {
  type = string
}

variable "media-pvc" {
  type = string
}

locals {
  namespace = "default"
  host = "ftp.${var.domain}"
}

resource "kubernetes_deployment" "ftp" {
  metadata {
    name = "ftp"
    namespace = local.namespace
  }
  spec {
    selector {
      match_labels = {
        app = "ftp"
      }
    }
    template {
      metadata {
        labels = {
          app = "ftp"
        }
      }
      spec {
        container {
          name = "main"
          image = "drakkan/sftpgo:v2.3.4"
          env {
            name = "SFTPGO_FTPD__BINDINGS__0__PORT"
            value = "2121"
          }
          env {
            name = "SFTPGO_HTTPD__BINDINGS__0__PORT"
            value = "8080"
          }
          volume_mount {
            name = "media"
            mount_path = "/media"
          }
        }
        volume {
          name = "media"
          persistent_volume_claim {
            claim_name = var.media-pvc
          }
        }
        volume {
          name = "ftp"
          persistent_volume_claim {
            claim_name = kubernetes_persistent_volume_claim.ftp.metadata[0].name
          }
        }
        volume {
          name = "config"
          config_map {
            name = kubernetes_config_map.ftp.metadata[0].name
          }
        }
      }
    }
  }
}

resource "kubernetes_service" "ftp" {
  metadata {
    name = "ftp"
    namespace = local.namespace
  }
  spec {
    selector = {
      app = "ftp"
    }
    port {
      port = TODO
      name = "http"
    }
  }
}

resource "kubernetes_ingress" "ftp" {
  metadata {
    name = "ftp"
    namespace = local.namespace
  }
  spec {
    rule {
      host = local.host
      http {
        path {
          path = "/"
          backend {
            service_name = kubernetes_service.ftp.metadata[0].name
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