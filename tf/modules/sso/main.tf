variable "domain" {
  type = string
  default = "k8s.local"
}

variable "keycloak-admin-password" {
  type = string
}

variable "keycloak-oidc-secret" {
  type = string
  description = "Give some placeholder initially, then set up in the keycloak webui. See https://wjw465150.gitbooks.io/keycloak-documentation/content/server_admin/topics/clients/client-oidc.html (+ subpages, esp 3.8.1.1)"
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
  vouch_host = "vouch.${var.domain}"
  keycloak_host = "keycloak.${var.domain}"
}

output "vouch_host" {
  value = local.vouch_host
}

output "keycloak_host" {
  value = local.keycloak_host
}
