variable "domain" {
  type = string
}

locals {
  namespace = "default"
}

resource "random_password" "mariadb" {
  length = 30
}

resource "helm_release" "mariadb" {
  repository = "https://charts.bitnami.com/bitnami"
  chart = "mariadb"
  version = "11.1.0"

  name = "mariadb"
  namespace = local.namespace

  values = [yamlencode({
    clusterDomain: var.domain
    auth: {
      rootPassword: random_password.mariadb.result
    }
    primary: {
      persistence: {
        size: "50Gi"
      }
    }
  })]
}

output "user" {
  value = "root"
}

output "password" {
  value = random_password.mariadb.result
}

output "port" {
  value = 3306
}

output "service" {
  value = "mariadb"
}