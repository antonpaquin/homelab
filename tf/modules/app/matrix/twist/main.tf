variable "domain" {
  type = string
}

variable "homeserver" {
  type = string
}

variable "tls_secret" {
  type = string
}

locals {
  namespace = "default"
  host = "matrix-twist.${var.domain}"
}

resource "kubernetes_config_map" "matrix-twist" {
  metadata {
    name = "matrix-twist"
    namespace = local.namespace
  }
  data = {
    "config.json" = jsonencode({})
  }
}

resource "kubernetes_deployment" "matrix-twist" {
  metadata {
    name = "matrix-twist"
    namespace = local.namespace
  }
  spec {
    selector {
      match_labels = {
        app = "matrix-twist"
      }
    }
    template {
      metadata {
        labels = {
          app = "matrix-twist"
        }
      }
      spec {
        container {
          name = "main"
          image = ""
          volume_mount {
            mount_path = "/opt/matrix-twist/config.json"
            name = "config"
            sub_path = "config.json"
          }
        }
        volume {
          name = "config"
          config_map {
            name = kubernetes_config_map.matrix-twist.metadata[0].name
          }
        }
      }
    }
  }
}

resource "kubernetes_service" "matrix-twist" {
  metadata {
    name = "matrix-twist"
    namespace = local.namespace
  }
  spec {
    selector = {
      app = "matrix-twist"
    }
    port {
      port = 8080
      name = "http"
    }
  }
}

resource "kubernetes_ingress_v1" "matrix-twist" {
  metadata {
    name = "matrix-twist"
    namespace = local.namespace
  }
  spec {
    tls {
      secret_name = var.tls_secret
    }
    rule {
      host = local.host
      http {
        path {
          path = "/"
          backend {
            service_name = kubernetes_service.matrix-twist.metadata[0].name
            service_port = "http"
          }
        }
      }
    }
  }
}

