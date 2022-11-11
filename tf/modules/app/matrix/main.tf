variable "domain" {
  type = string
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
    synapse = object({
      registration_shared_secret = string
      macaroon_secret_key = string
      form_secret = string
      signing_key = string
    })
  })
}

variable "sso_oidc_params" {
  type = object({
    name: string
    issuer: string
    client_id: string
    client_secret: string
  })
}

variable "tls_secret" {
  type = string
}

module "synapse" {
  source = "./synapse"
  domain = var.domain
  host_prefix = "matrix-synapse"
  matrix_client_host = "matrix-element.${var.domain}"
  postgres_database = var.postgres_database
  secret = var.secret.synapse
  sso_oidc_params = var.sso_oidc_params
  tls_secret = var.tls_secret
}

module "element" {
  source = "./element"
  domain = var.domain
  homeserver = "matrix-synapse.${var.domain}"
  tls_secret = var.tls_secret
}