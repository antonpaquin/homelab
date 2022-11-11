variable "domain" {
  type = string
}

variable "matrix_client_host" {
  type = string
}

variable "host_prefix" {
  type = string
}

variable "sso_oidc_params" {
  type = object({
    name: string
    issuer: string
    client_id: string
    client_secret: string
  })
}

variable "postgres_database" {
  type = object({
    username = string
    password = string
    host = string
    port = number
    dbname = string
  })
}

variable "secret" {
  type = object({
    registration_shared_secret = string
    macaroon_secret_key = string
    form_secret = string
    signing_key = string
  })
}

variable "tls_secret" {
  type = string
}

locals {
  namespace = "default"
  host = "${var.host_prefix}.${var.domain}"

  signing_key_fname = "${local.host}.signing.key"
  log_config_fname = "${local.host}.log.config"
}

resource "kubernetes_secret" "matrix-synapse" {
  metadata {
    name = "matrix-synapse"
    namespace = local.namespace
  }
  data = {
    (local.signing_key_fname) = var.secret.signing_key
    (local.log_config_fname) = file("${path.module}/log.config.yaml")
    "homeserver.yaml" = templatefile("${path.module}/homeserver.yaml", {
      domain = var.domain
      host = local.host
      matrix_client_host = var.matrix_client_host

      db_uname = var.postgres_database.username
      db_password = var.postgres_database.password
      db_host = var.postgres_database.host
      db_port = var.postgres_database.port
      db_dbname = var.postgres_database.dbname

      sso_oidc_name = var.sso_oidc_params.name
      sso_oidc_issuer = var.sso_oidc_params.issuer
      sso_oidc_client_id = var.sso_oidc_params.client_id
      sso_oidc_client_secret = var.sso_oidc_params.client_secret

      registration_shared_secret = var.secret.registration_shared_secret
      macaroon_secret_key = var.secret.macaroon_secret_key
      form_secret = var.secret.form_secret

      log_config_fname = local.log_config_fname
      signing_key_fname = local.signing_key_fname
    })
  }
}

resource "kubernetes_persistent_volume_claim" "matrix-synapse" {
  metadata {
    name = "matrix-synapse"
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

module "initdb" {
  source = "../../../../modules/app_infra/initdb"
  name = "matrix-synapse"
  db = var.postgres_database
  locale = "C"
  encoding = "UTF8"
  template = "template0"
}

resource "kubernetes_deployment" "matrix-synapse" {
  wait_for_rollout = false
  metadata {
    name = "matrix-synapse"
    namespace = local.namespace
  }
  spec {
    selector {
      match_labels = {
        app = "matrix-synapse"
      }
    }
    template {
      metadata {
        labels = {
          app = "matrix-synapse"
        }
      }
      spec {
        container {
          name = "main"
          image = "docker.io/matrixdotorg/synapse:v1.62.0"
          env {
            name = "SYNAPSE_SERVER_NAME"
            value = local.host
          }
          env {
            name = "SYNAPSE_CONFIG_DIR"
            value = "/config"
          }
          env {
            name = "UID"
            value = "1000"
          }
          env {
            name = "GID"
            value = "1000"
          }
          volume_mount {
            name = "matrix-synapse"
            mount_path = "/data"
          }
          volume_mount {
            mount_path = "/config"
            name = "config"
          }
        }
        volume {
          name = "matrix-synapse"
          persistent_volume_claim {
            claim_name = kubernetes_persistent_volume_claim.matrix-synapse.metadata[0].name
          }
        }
        volume {
          name = "config"
          secret {
            secret_name = kubernetes_secret.matrix-synapse.metadata[0].name
          }
        }
      }
    }
  }
}

resource "kubernetes_service" "matrix-synapse" {
  metadata {
    name = "matrix-synapse"
    namespace = local.namespace
  }
  spec {
    selector = {
      app = "matrix-synapse"
    }
    port {
      port = 80
      name = "http"
    }
  }
}

resource "kubernetes_service" "matrix-synapse-federation" {
  metadata {
    name = "matrix-synapse-federation"
    namespace = local.namespace
  }
  spec {
    selector = {
      app = "matrix-synapse"
    }
    port {
      port = 8448
      node_port = 8448
      name = "federation"
    }
    type = "NodePort"
  }
}

resource "kubernetes_ingress" "matrix-synapse" {
  metadata {
    name = "matrix-synapse"
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
            service_name = kubernetes_service.matrix-synapse.metadata[0].name
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
