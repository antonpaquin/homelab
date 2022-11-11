module "backup" {
  source = "../../modules/app/backup"
  aws_backup_bucket = local.aws_backup_bucket
  backup_secrets = local.secret["backup"]
  aws_secrets = local.secret["aws"]["s3-full"]
  media-pvc = module.media.claim-name
}

module "blog" {
  depends_on = [module.mariadb]
  source = "../../modules/app/blog"
  domain = local.domain
  database = {
    username = module.mariadb.user
    password = module.mariadb.password
    host = module.mariadb.service
    port = module.mariadb.port
    dbname = "blog"
  }
  tls_secret = local.tls_secrets.default.name
  wp_secret_seed = local.secret["wordpress"]["seed"]
}

module "dad-ffmpeg" {
  source = "../../modules/app/dad-ffmpeg"
}

module "deluge" {
  source = "../../modules/app/deluge"
  authproxy_host = module.authproxy-default.host
  media-pvc = module.media.claim-name
  domain = local.domain
  tls_secret = local.tls_secrets.default.name
}

module "filebrowser" {
  source = "../../modules/app/filebrowser"
  authproxy_host = module.authproxy-default.host
  media-pvc = module.media.claim-name
  domain = local.domain
  tls_secret = local.tls_secrets.default.name
}

module "grafana" {
  source = "../../modules/app/grafana"
  authproxy_host = module.authproxy-default.host
  prometheus_url = "http://${module.prometheus.service}"
  domain = local.domain
  tls_secret = local.tls_secrets.default.name
}

module "grocy" {
  source = "../../modules/app/grocy"
  authproxy_host = module.authproxy-default.host
  domain = local.domain
  tls_secret = local.tls_secrets.default.name
}

module "hardlinker" {
  source = "../../modules/app/hardlinker"
  media-pvc = module.media.claim-name
  domain = local.domain
  authproxy_host = module.authproxy-default.host
  tls_secret = local.tls_secrets.default.name
}

module "jellyfin" {
  source = "../../modules/app/jellyfin"
  authproxy_host = module.authproxy-default.host
  domain = local.domain
  media-pvc = module.media.claim-name
  tls_secret = local.tls_secrets.default.name
}
module "komga" {
  source = "../../modules/app/komga"
  authproxy_host = module.authproxy-default.host
  domain = local.domain
  media-pvc = module.media.claim-name
  tls_secret = local.tls_secrets.default.name
}

module "matrix" {
  source = "../../modules/app/matrix"
  domain = local.domain
  postgres_database = {
    username = module.postgresql.user
    password = module.postgresql.password
    host = module.postgresql.host
    port = module.postgresql.port
    dbname = "matrix"
  }
  secret = {
    synapse = {
      registration_shared_secret = local.secret["matrix"]["synapse"]["registration_shared_secret"]
      macaroon_secret_key = local.secret["matrix"]["synapse"]["macaroon_secret_key"]
      form_secret = local.secret["matrix"]["synapse"]["form_secret"]
      signing_key = local.secret["matrix"]["synapse"]["signing_key"]
    }
  }
  sso_oidc_params = {
    name: "matrix-synapse"
    issuer: "https://keycloak.${local.domain}/realms/default"
    client_id: "matrix-synapse"
    client_secret: local.secret["keycloak"]["synapse-oidc-secret"]
  }
  tls_secret = local.tls_secrets.default.name
}

module "media-srv" {
  source = "../../modules/app/media_srv"
  domain = local.domain
  media-pvc = module.media.claim-name
}

module "metube" {
  source = "../../modules/app/metube"
  authproxy_host = module.authproxy-default.host
  domain = local.domain
  media-pvc = module.media.claim-name
  tls_secret = local.tls_secrets.default.name
}

module "photoprism" {
  depends_on = [module.mariadb]
  source = "../../modules/app/photoprism"
  domain = local.domain
  authproxy_host = module.authproxy-default.host
  database = {
    username = module.mariadb.user
    password = module.mariadb.password
    host = module.mariadb.service
    port = module.mariadb.port
    dbname = "photoprism"
  }
  media-pvc = module.media.claim-name
  tls_secret = local.tls_secrets.default.name
}

module "shell" {
  source = "../../modules/app/shell"
  media-pvc = module.media.claim-name
  backup-pvc = module.volumes.backup-claim-name
}

module "sonarr" {
  source = "../../modules/app/sonarr"
  authproxy_host = module.authproxy-default.host
  domain = local.domain
  media-pvc = module.media.claim-name
  tls_secret = local.tls_secrets.default.name
}

module "stable-diffusion" {
  source = "../../modules/app/stable-diffusion"
  domain = local.domain
  authproxy_host = module.authproxy-default.host
  tls_secret = local.tls_secrets.default.name
}

module "tandoor" {
  source = "../../modules/app/tandoor"
  authproxy_host = module.authproxy-default.host
  domain = local.domain
  database = {
    username = module.postgresql.user
    password = module.postgresql.password
    host = module.postgresql.host
    port = module.postgresql.port
    dbname = "tandoor"
  }
  tls_secret = local.tls_secrets.default.name
}
