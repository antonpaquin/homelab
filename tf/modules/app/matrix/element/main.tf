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
  host = "matrix-element.${var.domain}"
}

resource "kubernetes_config_map" "matrix-element" {
  metadata {
    name = "matrix-element"
    namespace = local.namespace
  }
  data = {
    "config.json" = jsonencode(merge(jsondecode(file("${path.module}/default_config.json")), {
      "default_server_config": {
        "m.homeserver": {
           "base_url": "https://${var.homeserver}"
        },
        "default_server_name": var.homeserver,
        "default_theme": "dark",
        "permalink_prefix": "https://${var.homeserver}"
        "mobile_guide_toast": false,
      }
    }))
  }
}

resource "kubernetes_deployment" "matrix-element" {
  metadata {
    name = "matrix-element"
    namespace = local.namespace
  }
  spec {
    selector {
      match_labels = {
        app = "matrix-element"
      }
    }
    template {
      metadata {
        labels = {
          app = "matrix-element"
        }
      }
      spec {
        container {
          name = "main"
          image = "docker.io/vectorim/element-web:v1.11.0"
          volume_mount {
            mount_path = "/app/config.json"
            name = "config"
            sub_path = "config.json"
          }
        }
        volume {
          name = "config"
          config_map {
            name = kubernetes_config_map.matrix-element.metadata[0].name
          }
        }
      }
    }
  }
}

resource "kubernetes_service" "matrix-element" {
  metadata {
    name = "matrix-element"
    namespace = local.namespace
  }
  spec {
    selector = {
      app = "matrix-element"
    }
    port {
      port = 80
      name = "http"
    }
  }
}

resource "kubernetes_ingress" "matrix-element" {
  metadata {
    name = "matrix-element"
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
            service_name = kubernetes_service.matrix-element.metadata[0].name
            service_port = "http"
          }
        }
      }
    }
  }
}

