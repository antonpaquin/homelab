variable "domain" {
  type = string
}

locals {
  namespace = "default"
}

variable "password" {
  type = string
}


resource "helm_release" "mariadb" {
  wait = false
  wait_for_jobs = false
  repository = "https://charts.bitnami.com/bitnami"
  chart = "mariadb"
  version = "11.1.0"

  name = "mariadb"
  namespace = local.namespace

  values = [yamlencode({
    clusterDomain: var.domain
    auth: {
      rootPassword: var.password
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
  sensitive = true
  value = var.password
}

output "port" {
  value = 3306
}

output "service" {
  value = "mariadb"
}