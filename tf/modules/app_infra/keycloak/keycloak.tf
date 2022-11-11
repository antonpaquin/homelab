locals {
  db_name = "keycloak"
}

# for some reason keycloak is redirecting / to /auth which is 404?
# go to /admin instead

resource "kubernetes_secret" "keycloak" {
  metadata {
    name = "keycloak-secrets"
    namespace = local.namespace
  }
  data = {
    KEYCLOAK_ADMIN = "admin"
    KEYCLOAK_ADMIN_PASSWORD = var.keycloak-admin-password

    KC_DB = var.keycloak-db.vendor
    KC_DB_URL = local.jdbc_url
    KC_DB_USERNAME = var.keycloak-db.user
    KC_DB_PASSWORD = var.keycloak-db.password

    KC_HOSTNAME = local.keycloak_host
    KC_HOSTNAME_STRICT_HTTPS = "false"
    KC_HTTP_ENABLED = "true"
    KC_HEALTH_ENABLED = "true"
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

export PGPASSWORD="$KC_DB_PASSWORD"
psql \
  --username="$KC_DB_USERNAME" \
  --no-password \
  --host="${var.keycloak-db.host}" \
  --port="${var.keycloak-db.port}" \
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
          image = "postgres:14.4"
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
          image = "quay.io/keycloak/keycloak:18.0.2"
          env_from {
            secret_ref {
              name = kubernetes_secret.keycloak.metadata[0].name
              optional = false
            }
          }
          args = [
            "start",
            "--auto-build",
            "--proxy", "edge",
            "--db-url", local.jdbc_url,
          ]
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
    tls {
      secret_name = var.tls_secret
    }
  }
}
