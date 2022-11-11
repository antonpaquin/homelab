variable "domain" {
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

variable "wp_secret_seed" {
  type = string
}

variable "tls_secret" {
  type = string
}

locals {
  namespace = "default"
  host = "blog.${var.domain}"
}

locals {
  secret_auth_key = sha256(join("", [var.wp_secret_seed, "auth_key"]))
  secret_secure_auth_key = sha256(join("", [var.wp_secret_seed, "secure_auth_key"]))
  secret_logged_in_key = sha256(join("", [var.wp_secret_seed, "logged_in_key"]))
  secret_nonce_key = sha256(join("", [var.wp_secret_seed, "nonce_key"]))
  secret_auth_salt = sha256(join("", [var.wp_secret_seed, "auth_salt"]))
  secret_secure_auth_salt = sha256(join("", [var.wp_secret_seed, "secure_auth_salt"]))
  secret_logged_in_salt = sha256(join("", [var.wp_secret_seed, "logged_in_salt"]))
  secret_nonce_salt = sha256(join("", [var.wp_secret_seed, "nonce_salt"]))
}

resource "kubernetes_persistent_volume_claim" "blog" {
  metadata {
    name = "blog"
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

resource "kubernetes_config_map" "blog" {
  metadata {
    name = "blog"
    namespace = local.namespace
  }
  data = {
    WORDPRESS_DB_HOST: var.database.host
    WORDPRESS_DB_USER: var.database.username
    WORDPRESS_DB_PASSWORD: var.database.password
    WORDPRESS_DB_NAME: var.database.dbname
    WORDPRESS_TABLE_PREFIX: "61aa_wp_"

    WORDPRESS_AUTH_KEY: local.secret_auth_key
    WORDPRESS_SECURE_AUTH_KEY: local.secret_secure_auth_key
    WORDPRESS_LOGGED_IN_KEY: local.secret_logged_in_key
    WORDPRESS_NONCE_KEY: local.secret_nonce_key
    WORDPRESS_AUTH_SALT: local.secret_auth_salt
    WORDPRESS_SECURE_AUTH_SALT: local.secret_secure_auth_salt
    WORDPRESS_LOGGED_IN_SALT: local.secret_logged_in_salt
    WORDPRESS_NONCE_SALT: local.secret_nonce_salt
  }
}

resource "kubernetes_deployment" "blog" {
  metadata {
    name = "blog"
    namespace = local.namespace
  }
  spec {
    selector {
      match_labels = {
        app = "blog"
      }
    }
    template {
      metadata {
        labels = {
          app = "blog"
        }
      }
      spec {
        init_container {
          name = "initdb"
          image = "docker.io/bitnami/mariadb:10.5.11-debian-10-r0"
          env_from {
            config_map_ref {
              name = kubernetes_config_map.blog.metadata[0].name
            }
          }
          command = [
            "/bin/bash",
            "-c",
            join(" ", [
              "mysql",
              "--host=\"$WORDPRESS_DB_HOST\"",
              "--user=\"$WORDPRESS_DB_USER\"",
              "--password=\"$WORDPRESS_DB_PASSWORD\"",
              "-e",
              "\"CREATE DATABASE IF NOT EXISTS $WORDPRESS_DB_NAME\""
            ])
          ]
        }
        container {
          name = "main"
          image = "wordpress:5.9.1-apache"
          env_from {
            config_map_ref {
              name = kubernetes_config_map.blog.metadata[0].name
            }
          }
          volume_mount {
            name = "blog"
            mount_path = "/var/www/html"
          }
        }
        volume {
          name = "blog"
          persistent_volume_claim {
            claim_name = kubernetes_persistent_volume_claim.blog.metadata[0].name
          }
        }
      }
    }
  }
}

resource "kubernetes_service" "blog" {
  metadata {
    name = "blog"
    namespace = local.namespace
  }
  spec {
    selector = {
      app = "blog"
    }
    port {
      port = 80
      name = "http"
    }
  }
}

resource "kubernetes_ingress" "blog" {
  metadata {
    name = "blog"
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
            service_name = kubernetes_service.blog.metadata[0].name
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