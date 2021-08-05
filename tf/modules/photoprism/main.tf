variable "domain" {
  type = string
  default = "k8s.local"
}

variable "media-pvc" {
  type = string
}

variable "database" {
  type = object({
    username = string
    password = string
    host = string
    port = number
    dbname = string
  })
}

locals {
  namespace = "default"
  host = "photoprism.${var.domain}"
}

resource "kubernetes_secret" "photoprism" {
  metadata {
    name = "photoprism-secrets"
    namespace = local.namespace
  }
  data = {
    PHOTOPRISM_ADMIN_PASSWORD = "cirno9ball"
    PHOTOPRISM_DATABASE_SERVER: "${var.database.host}:${var.database.port}"
    PHOTOPRISM_DATABASE_NAME: var.database.dbname
    PHOTOPRISM_DATABASE_USER: var.database.username
    PHOTOPRISM_DATABASE_PASSWORD: var.database.password
  }
}

resource "kubernetes_config_map" "photoprism" {
  metadata {
    name = "photoprism"
    namespace = local.namespace
  }
  data = {
    PHOTOPRISM_DEBUG = "true"
    PHOTOPRISM_CACHE_PATH = "/cache"
    PHOTOPRISM_IMPORT_PATH = "/media/library/photos/import"
    PHOTOPRISM_EXPORT_PATH = "/media/library/photos/export"
    PHOTOPRISM_ORIGINALS_PATH = "/media/library/photos/originals"
    PHOTOPRISM_DATABASE_DRIVER = "mysql"
    PHOTOPRISM_HTTP_HOST = "0.0.0.0"
    PHOTOPRISM_HTTP_PORT = "2342"
  }
}

resource "kubernetes_config_map" "photoprism-initdb" {
  metadata {
    name = "photoprism-initdb"
    namespace = local.namespace
  }
  data = {
    "entrypoint.sh" = <<EOF
#! /bin/bash

mysql \
  --user="$PHOTOPRISM_DATABASE_USER" \
  --password="$PHOTOPRISM_DATABASE_PASSWORD" \
  --host="${var.database.host}" \
  --port="${var.database.port}" \
  < /initdb/init.sql
EOF
    "init.sql": <<EOF
CREATE DATABASE IF NOT EXISTS ${var.database.dbname};
EOF
  }
}

resource "kubernetes_stateful_set" "photoprism" {
  metadata {
    name = "photoprism"
    namespace = local.namespace
  }
  spec {
    service_name = "photoprism"
    replicas = 1
    selector {
      match_labels = {
        app = "photoprism"
      }
    }
    template {
      metadata {
        labels = {
          app = "photoprism"
        }
      }
      spec {
        init_container {
          name = "initdb"
          image = "docker.io/bitnami/mariadb:10.5.11-debian-10-r0"
          command = ["/initdb/entrypoint.sh"]
          env_from {
            secret_ref {
              name = kubernetes_secret.photoprism.metadata[0].name
              optional = false
            }
          }
          volume_mount {
            name = "initdb"
            mount_path = "/initdb"
          }
        }
        container {
          name = "photoprism"
          image = "photoprism/photoprism:latest"
          env_from {
            config_map_ref {
              name = kubernetes_config_map.photoprism.metadata[0].name
            }
          }
          env_from {
            secret_ref {
              name = kubernetes_secret.photoprism.metadata[0].name
              optional = false
            }
          }
          port {
            name = "http"
            container_port = 2342
          }
          volume_mount {
            mount_path = "/media"
            name = "media"
          }
          readiness_probe {
            http_get {
              path = "/api/v1/status"
              port = "http"
            }
          }
        }
        volume {
          name = "media"
          persistent_volume_claim {
            claim_name = var.media-pvc
          }
        }
        volume {
          name = "initdb"
          config_map {
            name = kubernetes_config_map.photoprism-initdb.metadata[0].name
            default_mode = "0777"
          }
        }
      }
    }
  }
}

resource "kubernetes_service" "photoprism" {
  metadata {
    name = "photoprism"
    namespace = local.namespace
  }
  spec {
    selector = {
      app = "photoprism"
    }
    type = "ClusterIP"
    port {
      name = "http"
      port = 80
      protocol = "TCP"
      target_port = "http"
    }
  }
}

resource "kubernetes_ingress" "photoprism" {
  metadata {
    name = "photoprism"
    namespace = local.namespace
    annotations = {
      "kubernetes.io/ingress.class" = "nginx"
      "nginx.ingress.kubernetes.io/proxy-body-size" = "512M"
    }
  }
  spec {
    rule {
      host = local.host
      http {
        path {
          path = "/"
          backend {
            service_name = "photoprism"
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
