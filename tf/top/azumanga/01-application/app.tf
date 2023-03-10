module "deluge" {
  source = "../../../modules/app/deluge"
  authproxy_host = module.authproxy-default.host
  media-pvc = module.volumes.media-claim-name
  domain = local.domain
  tls_secret = local.tls_secrets.default.name
}

module "filebrowser" {
  source = "../../../modules/app/filebrowser"
  authproxy_host = module.authproxy-default.host
  media-pvc = module.volumes.media-claim-name
  domain = local.domain
  tls_secret = local.tls_secrets.default.name
}

module "metube" {
  source = "../../../modules/app/metube"
  authproxy_host = module.authproxy-default.host
  domain = local.domain
  media-pvc = module.volumes.media-claim-name
  tls_secret = local.tls_secrets.default.name
}

module "photoprism" {
  depends_on = [module.mariadb]
  source = "../../../modules/app/photoprism"
  domain = local.domain
  authproxy_host = module.authproxy-default.host
  database = {
    username = module.mariadb.user
    password = module.mariadb.password
    host = module.mariadb.service
    port = module.mariadb.port
    dbname = "photoprism"
  }
  media-pvc = module.volumes.media-claim-name
  tls_secret = local.tls_secrets.default.name
}

module "shell" {
  source = "../../../modules/app/shell"
  media-pvc = module.volumes.media-claim-name
  backup-pvc = module.volumes.backup-claim-name
}
