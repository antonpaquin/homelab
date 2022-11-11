variable "domain" {
  type = string
  description = "Main domain of the cluster"
}

variable "namecheap-api-user" {
  type = string
  description = "Username for namecheap"
}

variable "namecheap-api-key" {
  type = string
  description = "API key for namecheap"
}

variable "certificate_secrets" {
  type = map(object({
    name: string
    namespace: string
  }))
}

locals {
  namespace = "ingress-nginx"
  schedule = "${random_integer.cronjob-jitter.result} 0 * * 0"  # Weekly on sunday, a bit after midnight (jitter is just politeness)

  config = {
    certificates: [
      for _, secret_spec in var.certificate_secrets:
      {
        name: secret_spec["name"],
        namespace: secret_spec["namespace"],
      }
    ]
    namecheap: {
      api_url: "https://api.namecheap.com/xml.response"
    }
    tls: {
      domain: "*.${var.domain}"
      email: "tls@antonpaqu.in"
      test: false
    }
  }
}

resource "random_integer" "cronjob-jitter" {
  min = 0
  max = 59
}

resource "kubernetes_secret" "namecheap-api-credentials" {
  metadata {
    name = "namecheap-api-credentials"
    namespace = local.namespace
  }
  data = {
    NAMECHEAP_API_KEY: var.namecheap-api-key
    NAMECHEAP_API_USER: var.namecheap-api-user
  }
}

resource "kubernetes_config_map" "renew-certificates-config" {
  metadata {
    name = "renew-certificates-config"
    namespace = local.namespace
  }
  data = {
    "config.json": jsonencode(local.config)
  }
}


resource "kubernetes_cluster_role" "renew-tls-certificates" {
  metadata {
    name = "renew-tls-certificates"
  }
  rule {
    api_groups = [""]
    resources = ["secrets"]
    verbs = ["create", "list", "update"]
  }
}

resource "kubernetes_cluster_role_binding" "renew-tls-certificates-binding" {
  metadata {
    name = "tls-admin-renew-tls-certificates"
  }
  role_ref {
    api_group = "rbac.authorization.k8s.io"
    kind = "ClusterRole"
    name = kubernetes_cluster_role.renew-tls-certificates.metadata[0].name
  }
  subject {
    kind = "ServiceAccount"
    name = kubernetes_service_account.tls-admin.metadata[0].name
    namespace = kubernetes_service_account.tls-admin.metadata[0].namespace
  }
}

resource "kubernetes_service_account" "tls-admin" {
  metadata {
    name = "tls-admin"
    namespace = local.namespace
  }
}

resource "kubernetes_cron_job" "renew-certificates" {
  metadata {
    name = "renew-certificates"
    namespace = local.namespace
  }
  spec {
    schedule = local.schedule
    job_template {
      metadata {}
      spec {
        backoff_limit = 1
        template {
          metadata {}
          spec {
            service_account_name = kubernetes_service_account.tls-admin.metadata[0].name
            restart_policy = "Never"
            container {
              name = "main"
              image_pull_policy = "Always"
              image = "antonpaquin/misc:certbot-namecheap"
              env {
                name = "CONFIG_FILE"
                value = "/config/config.json"
              }
              env_from {
                secret_ref {
                  name = kubernetes_secret.namecheap-api-credentials.metadata[0].name
                }
              }
              volume_mount {
                name = "config"
                mount_path = "/config/"
              }
            }
            volume {
              name = "config"
              config_map {
                name = kubernetes_config_map.renew-certificates-config.metadata[0].name
              }
            }
          }
        }
      }
    }
  }
}
