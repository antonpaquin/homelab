variable "domain" {
  type = string
}

variable "keycloak-admin-password" {
  type = string
}

variable "keycloak-db" {
  type = object({
    vendor = string
    host = string
    port = number
    user = string
    password = string
    dbname = string
  })
}

variable "tls_secret" {
  type = string
}

locals {
  namespace = "default"
  keycloak_host = "keycloak.${var.domain}"

  jdbc_url = "jdbc:postgresql://${var.keycloak-db.host}:${var.keycloak-db.port}/${var.keycloak-db.dbname}"
}

output "host" {
  value = local.keycloak_host
}
