variable "domain" {
  type = string
}

variable "media-pvc" {
  type = string
}

locals {
  namespace = "default"
  host = "media-srv.${var.domain}"
}

resource "kubernetes_config_map" "media-srv" {
  metadata {
    name = "media-srv"
    namespace = local.namespace
  }
  data = {
    "default.conf" = <<EOF
server {
    listen 80;
    location / {
        autoindex on;
        root /media/library;
    }
}
EOF
  }
}

resource "kubernetes_deployment" "media-srv" {
  metadata {
    name = "media-srv"
    namespace = local.namespace
  }
  spec {
    selector {
      match_labels = {
        app = "media-srv"
      }
    }
    template {
      metadata {
        labels = {
          app = "media-srv"
        }
      }
      spec {
        container {
          name = "main"
          image = "docker.io/nginx"
          volume_mount {
            name = "media"
            mount_path = "/media"
          }
          volume_mount {
            name = "config"
            mount_path = "/etc/nginx/conf.d"
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
          config_map {
            name = kubernetes_config_map.media-srv.metadata[0].name
          }
        }
      }
    }
  }
}

resource "kubernetes_service" "media-srv" {
  metadata {
    name = "media-srv"
    namespace = local.namespace
  }
  spec {
    selector = {
      app = "media-srv"
    }
    port {
      port = 80
      name = "http"
    }
  }
}

resource "kubernetes_ingress" "media-srv" {
  metadata {
    name = "media-srv"
    namespace = local.namespace
  }
  spec {
    rule {
      host = local.host
      http {
        path {
          path = "/"
          backend {
            service_name = kubernetes_service.media-srv.metadata[0].name
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
