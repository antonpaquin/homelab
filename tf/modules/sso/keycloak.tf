locals {
  db_name = "keycloak"
}

resource "kubernetes_secret" "keycloak" {
  metadata {
    name = "keycloak-secrets"
    namespace = local.namespace
  }
  data = {
    KEYCLOAK_USER = "admin"
    KEYCLOAK_PASSWORD = var.keycloak-admin-password
    DB_VENDOR = var.keycloak-db.vendor
    DB_ADDR = var.keycloak-db.host
    DB_PORT = var.keycloak-db.port
    DB_USER = var.keycloak-db.user
    DB_PASSWORD = var.keycloak-db.password
    DB_DATABASE = local.db_name
  }
}

resource "kubernetes_config_map" "keycloak-initdb" {
  metadata {
    name = "keycloak-initdb"
    namespace = local.namespace
  }
  data = {
    "entrypoint.sh" = <<EOF
#! /bin/bash

export PGPASSWORD="$DB_PASSWORD"
psql \
  --username="$DB_USER" \
  --no-password \
  --host="$DB_ADDR" \
  --port="$DB_PORT" \
  --dbname="postgres" \
  < /initdb/init.sql
EOF
    "init.sql": <<EOF
SELECT 'CREATE DATABASE ${local.db_name}'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '${local.db_name}')
\gexec
EOF
  }
}

resource "kubernetes_deployment" "keycloak" {
  metadata {
    name = "keycloak"
    namespace = local.namespace
  }
  spec {
    selector {
      match_labels = {
        app = "keycloak"
      }
    }
    template {
      metadata {
        labels = {
          app = "keycloak"
        }
      }
      spec {
        init_container {
          name = "initdb"
          image = "postgres:13.3"
          command = ["/initdb/entrypoint.sh"]
          env_from {
            secret_ref {
              name = kubernetes_secret.keycloak.metadata[0].name
              optional = false
            }
          }
          volume_mount {
            name = "initdb"
            mount_path = "/initdb"
          }
        }
        container {
          name = "main"
          image = "quay.io/keycloak/keycloak:14.0.0"
          env_from {
            secret_ref {
              name = kubernetes_secret.keycloak.metadata[0].name
              optional = false
            }
          }
        }
        volume {
          name = "initdb"
          config_map {
            name = kubernetes_config_map.keycloak-initdb.metadata[0].name
            default_mode = "0777"
          }
        }
      }
    }
  }
}

resource "kubernetes_service" "keycloak" {
  metadata {
    name = "keycloak"
    namespace = local.namespace
  }
  spec {
    selector = {
      app = "keycloak"
    }
    port {
      port = 8080
      name = "http"
    }
  }
}

resource "kubernetes_ingress" "keycloak" {
  metadata {
    name = "keycloak"
    namespace = local.namespace
  }
  spec {
    rule {
      host = local.keycloak_host
      http {
        path {
          path = "/"
          backend {
            service_name = kubernetes_service.keycloak.metadata[0].name
            service_port = "http"
          }
        }
      }
    }
  }
}
