locals {
  namespace = "default"
  user = "postgres"
  port = 5432
}

resource "random_password" "postgresql" {
  length = 30
}

resource "helm_release" "postgres" {
  repository = "https://charts.bitnami.com/bitnami"
  chart = "postgresql"
  version = "10.7.1"

  name = "postgres"
  namespace = local.namespace

  values = [yamlencode({
    postregsqlUsername = local.user
    postgresqlPassword = random_password.postgresql.result
    postgresqlDatabase = "postgres"
    service = {
      port = local.port
    }
    persistence = {
      size = "10Gi"
    }
    metrics = {
      enabled = true
    }
    securityContext: {
      enabled = true
      fsGroup = 1000
    }
    containerSecurityContext: {
      enabled = true
      runAsUser = 1000
    }
  })]
}

output "user" {
  value = local.user
}

output "password" {
  value = random_password.postgresql.result
}

output "host" {
  value = "postgres-postgresql"
}

output "port" {
  value = local.port
}
