variable "db" {
  type = object({
    host = string
    port = number
    username = string
    password = string
    dbname = string
  })
}

variable "encoding" {
  type = string
  default = ""
}

variable "locale" {
  type = string
  default = ""
}

variable "template" {
  type = string
  default = ""
}

variable "name" {
  type = string
}

locals {
  namespace = "default"
  name = "${var.name}-initdb"
}

locals {
  opt_encoding = var.encoding != "" ? "ENCODING \"${var.encoding}\"" : ""
  opt_locale = var.locale != "" ? "LOCALE \"${var.locale}\"" : ""
  opt_template = var.template != "" ? "TEMPLATE ${var.template}" : ""
}


resource "kubernetes_config_map" "initdb" {
  metadata {
    name = local.name
    namespace = local.namespace
  }
  data = {
    "entrypoint.sh" = <<EOF
#! /bin/bash

export PGPASSWORD="$DB_PASSWORD"
psql \
  --username="$DB_USERNAME" \
  --no-password \
  --host="${var.db.host}" \
  --port="${var.db.port}" \
  --dbname="postgres" \
  < /initdb/init.sql
EOF
    "init.sql": <<EOF
SELECT 'CREATE DATABASE ${var.db.dbname} ${local.opt_encoding} ${local.opt_locale} ${local.opt_template}'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '${var.db.dbname}')
\gexec
EOF
  }
}

resource "kubernetes_secret" "initdb" {
  metadata {
    name = local.name
    namespace = local.namespace
  }
  data = {
    DB_USERNAME = var.db.username
    DB_PASSWORD = var.db.password
  }
}


resource "kubernetes_job" "initdb" {
  wait_for_completion = false
  metadata {
    name = local.name
    namespace = local.namespace
  }
  spec {
    template {
      metadata {
        labels = {
          app = local.name
        }
      }
      spec {
        container {
          name = "initdb"
          image = "docker.io/postgres:14.4"
          command = ["/initdb/entrypoint.sh"]
          env_from {
            secret_ref {
              name = kubernetes_secret.initdb.metadata[0].name
              optional = false
            }
          }
          volume_mount {
            name = "initdb"
            mount_path = "/initdb"
          }
        }
        volume {
          name = "initdb"
          config_map {
            name = kubernetes_config_map.initdb.metadata[0].name
            default_mode = "0777"
          }
        }
      }
    }
  }
}

