variable "domain" {
  type = string
  default = "k8s.local"
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
  })
}

locals {
  namespace = "default"
  keycloak_host = "keycloak.${var.domain}"
}

output "host" {
  value = local.keycloak_host
}
