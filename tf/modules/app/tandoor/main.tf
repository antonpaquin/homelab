variable "domain" {
  type = string
}

variable "authproxy_host" {
  type = string
  description = "Authproxy host (for protected ingress)"
}

variable "tls_secret" {
  type = string
  description = "Secret containing a wildcard certificate of the type kubernetes.io/tls"
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
  host = "tandoor.${var.domain}"

  authproxy_user_header = "X-User"
  init_admin_user = "anton"
  init_admin_email = "scratch@antonpaqu.in"
}

resource "random_uuid" "tandoor-secret" {
}

resource "kubernetes_config_map" "tandoor-init" {
  metadata {
    name = "tandoor-initdb"
    namespace = local.namespace
  }
  data = {
    "initdb.sh" = <<EOF
#! /bin/bash

export PGPASSWORD="${var.database.password}"
psql \
  --username="${var.database.username}" \
  --no-password \
  --host="${var.database.host}" \
  --port="${var.database.port}" \
  --dbname="postgres" \
  < /init/initdb.sql
EOF
    "initdb.sql": <<EOF
SELECT 'CREATE DATABASE ${var.database.dbname}'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '${var.database.dbname}')
\gexec
EOF
    "inituser.sh": <<EOF
#! /bin/sh

source venv/bin/activate
python manage.py createsuperuser --username "${local.init_admin_user}" --email "${local.init_admin_email}" --noinput || true
exec /opt/recipes/boot.sh
EOF
  }
}

resource "kubernetes_secret" "tandoor" {
  metadata {
    name = "tandoor"
    namespace = local.namespace
  }
  data = {
    SECRET_KEY = random_uuid.tandoor-secret.result
    DB_ENGINE = "django.db.backends.postgresql"
    POSTGRES_HOST = var.database.host
    POSTGRES_PORT = var.database.port
    POSTGRES_USER = var.database.username
    POSTGRES_PASSWORD = var.database.password
    POSTGRES_DB = var.database.dbname

    REVERSE_PROXY_AUTH = "1"
    PROXY_HEADER = join("", ["HTTP_", upper(replace(local.authproxy_user_header, "-", "_"))])
  }
}

resource "kubernetes_persistent_volume_claim" "tandoor" {
  metadata {
    name = "tandoor"
    namespace = local.namespace
  }
  spec {
    access_modes = ["ReadWriteOnce"]
    resources {
      requests = {
        storage = "10Gi"
      }
    }
  }
}

resource "kubernetes_deployment" "tandoor" {
  wait_for_rollout = false
  metadata {
    name = "tandoor"
    namespace = local.namespace
  }
  spec {
    selector {
      match_labels = {
        app = "tandoor"
      }
    }
    template {
      metadata {
        labels = {
          app = "tandoor"
        }
      }
      spec {
        init_container {
          name = "initdb"
          image = "docker.io/postgres:13.3"
          command = ["/init/initdb.sh"]
          volume_mount {
            name = "init"
            mount_path = "/init"
          }
        }
        container {
          name = "main"
          image = "docker.io/vabene1111/recipes:1.1.2"
          command = ["/init/inituser.sh"]
          env_from {
            secret_ref {
              name = kubernetes_secret.tandoor.metadata[0].name
            }
          }
          volume_mount {
            name = "tandoor"
            mount_path = "/opt/recipes/staticfiles"
            sub_path = "staticfiles"
          }
          volume_mount {
            name = "tandoor"
            mount_path = "/opt/recipes/mediafiles"
            sub_path = "mediafiles"
          }
          volume_mount {
            name = "init"
            mount_path = "/init"
          }
        }
        volume {
          name = "tandoor"
          persistent_volume_claim {
            claim_name = kubernetes_persistent_volume_claim.tandoor.metadata[0].name
          }
        }
        volume {
          name = "init"
          config_map {
            name = kubernetes_config_map.tandoor-init.metadata[0].name
            default_mode = "0777"
          }
        }
      }
    }
  }
}

resource "kubernetes_service" "tandoor" {
  metadata {
    name = "tandoorsvc"  # named weird because the autogenerated service env vars are screwing with config
    namespace = local.namespace
  }
  spec {
    selector = {
      app = "tandoor"
    }
    port {
      port = 8080
      name = "http"
    }
  }
}

module "protected_ingress" {
  source = "../../../modules/app_infra/authproxy/protected_ingress"
  host = local.host
  authproxy_host = var.authproxy_host
  namespace = local.namespace
  name = "tandoor"
  service_name = kubernetes_service.tandoor.metadata[0].name
  service_port = "http"
  tls_secret = var.tls_secret
  extra_annotations = {
    "nginx.ingress.kubernetes.io/configuration-snippet": join("\n", [
      "auth_request_set $auth_resp_user $upstream_http_x_authproxy_user;",
      "proxy_set_header ${local.authproxy_user_header} $auth_resp_user;"
    ])
  }
}

output "host" {
  value = local.host
}