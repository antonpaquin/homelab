module "cadvisor" {
  source = "../../../modules/app_infra/cadvisor"
}

module "keycloak" {
  depends_on = [module.postgresql]
  domain = local.domain
  source = "../../../modules/app_infra/keycloak"
  keycloak-admin-password = local.secret["keycloak"]["admin"]
  keycloak-db = {
    vendor = "postgres"
    user = module.postgresql.user
    password = module.postgresql.password
    host = module.postgresql.host
    port = module.postgresql.port
    dbname = "keycloak"
  }
  tls_secret = local.tls_secrets.default.name
}

module "logserv" {
  # Echoes back the request, basically
  authproxy_host = module.authproxy-default.host
  source = "../../../modules/app_infra/logserv"
  domain = local.domain
  tls_secret = local.tls_secrets.default.name
}

module "mariadb" {
  source = "../../../modules/app_infra/mariadb"
  domain = local.domain
  password = local.secret["mariadb"]["password"]
}

module "postgresql" {
  source = "../../../modules/app_infra/postgresql"
  password = local.secret["postgres"]["password"]
}
