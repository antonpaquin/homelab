locals {
  namespace = "default"
  user = "postgres"
  port = 5432
}

variable "password" {
  type = string
}

resource "helm_release" "postgres" {
  wait = false
  wait_for_jobs = false
  repository = "https://charts.bitnami.com/bitnami"
  chart = "postgresql"
  # bitnami has been bumping out old versions from the repo. Mirror?
  # Upgrading postgres is painful. See https://www.postgresql.org/docs/10/pgupgrade.html
  version = "11.6.18"

  name = "postgres"
  namespace = local.namespace

  values = [yamlencode({
    global = {
      postgresql = {
        auth = {
          username = local.user
          password = var.password
          database = "postgres"
        }
      }
    }
    auth = {  # required for metrics...?
      database = "_auth"
    }
    service = {
      ports = {
        postgresql = 5432
      }
    }
    persistence = {
      size = "10Gi"
    }
    metrics = {
      enabled = true
    }
    primary = {
      # for some bizarre reason, the chart defaults to 1001
      # expandingbrain.jpg
      containerSecurityContext: {
        enabled = true
        runAsUser = 1000
      }
      podSecurityContext: {
        enabled = true
        fsGroup = 1000
      }
    }
  })]
}

output "user" {
  value = local.user
}

output "password" {
  sensitive = true
  value = var.password
}

output "host" {
  value = "postgres-postgresql"
}

output "port" {
  value = local.port
}
