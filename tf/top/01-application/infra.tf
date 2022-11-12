module "authproxy-default" {
  depends_on = [module.keycloak]
  source = "../../modules/app_infra/authproxy/app"
  keycloak-oidc = {
    client-id = "authproxy-oidc"
    client-secret = local.secret["keycloak"]["authproxy-oidc-secret"]
  }
  authproxy_host = "authproxy.${local.domain}"
  domain = local.domain
  namespace = "default"
  tls_secret = local.tls_secrets.default.name
}

module "cadvisor" {
  source = "../../modules/app_infra/cadvisor"
}

module "certbot-namecheap" {
  source = "../../modules/app_infra/certbot-namecheap"
  domain = local.domain
  namecheap-api-user = local.secret["namecheap"]["user"]
  namecheap-api-key = local.secret["namecheap"]["api-key"]
  certificate_secrets = local.tls_secrets
}

module "devpi" {
  source = "../../modules/app_infra/devpi"
  domain = local.domain
}

module "keycloak" {
  depends_on = [module.postgresql]
  domain = local.domain
  source = "../../modules/app_infra/keycloak"
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
  source = "../../modules/app_infra/logserv"
  domain = local.domain
  tls_secret = local.tls_secrets.default.name
}

module "mariadb" {
  source = "../../modules/app_infra/mariadb"
  domain = local.domain
  password = local.secret["mariadb"]["password"]
}

module "postgresql" {
  source = "../../modules/app_infra/postgresql"
  password = local.secret["postgres"]["password"]
}

module "prometheus" {
  source = "../../modules/app_infra/prometheus"
  domain = local.domain
  tls_secret = local.tls_secrets.default.name
}

module "sshjump" {
  source = "../../modules/k8s_infra/sshjump"
  private-key = local.secret["ssh-jump"]["private-key"]
  remote-user = "root"
  remote-port = "22"
  remote-host = "util.antonpaqu.in"
  forward-destination = local.cluster.reimu-00.local-ip-address
  traffic-ports = [80, 443, 8448]
}

module "volumes" {
  source = "../../modules/volumes"
  backup-size = "1Ti"
}
