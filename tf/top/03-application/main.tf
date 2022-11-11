locals {
  secret = yamldecode(file("../../secret.yaml"))
  domain = "antonpaqu.in"

  cluster = {
    reimu = {
      local-ip-address = "192.168.0.102"
    }
    hakurei = {
      local-ip-address = "192.168.0.103"
    }
    reimu-00 = {
      local-ip-address = "192.168.0.104"
    }
  }

  aws_backup_bucket = "antonpaquin-backup"

  tls_secrets = {
    default: {name: "tls-cert", namespace: "default"}
    rook: {name: "tls-cert", namespace: "rook"}
  }
}

module "sshjump" {
  source = "../../modules/sshjump"
  private-key = local.secret["ssh-jump"]["private-key"]
  remote-user = "root"
  remote-port = "22"
  remote-host = "util.antonpaqu.in"
  forward-destination = local.cluster.reimu-00.local-ip-address
  traffic-ports = [80, 443, 8448]
}

# module "authproxy-ceph" {
#   depends_on = [module.keycloak, module.authproxy-default]
#   source = "../../modules/authproxy/app"
#   keycloak-oidc = {
#     client-id = "authproxy-ceph-oidc"
#     client-secret = local.secret["keycloak"]["authproxy-ceph-oidc-secret"]
#   }
#   authproxy_host = "authproxy-ceph.${local.domain}"
#   domain = local.domain
#   namespace = "rook"
# }

module "authproxy-default" {
  depends_on = [module.keycloak]
  source = "../../modules/authproxy/app"
  keycloak-oidc = {
    client-id = "authproxy-oidc"
    client-secret = local.secret["keycloak"]["authproxy-oidc-secret"]
  }
  authproxy_host = "authproxy.${local.domain}"
  domain = local.domain
  namespace = "default"
  tls_secret = local.tls_secrets.default.name
}

module "backup" {
  source = "../../modules/backup/app"
  aws_backup_bucket = local.aws_backup_bucket
  backup_secrets = local.secret["backup"]
  aws_secrets = local.secret["aws"]["s3-full"]
  media-pvc = module.media.claim-name
}

module "blog" {
  depends_on = [module.mariadb]
  source = "../../modules/blog"
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

module "cadvisor" {
  source = "../../modules/cadvisor"
}

module "certbot-namecheap" {
  source = "../../modules/certbot-namecheap"
  domain = local.domain
  namecheap-api-user = local.secret["namecheap"]["user"]
  namecheap-api-key = local.secret["namecheap"]["api-key"]
  certificate_secrets = local.tls_secrets
}

module "dad-ffmpeg" {
  source = "../../modules/dad-ffmpeg"
}

module "deluge" {
  source = "../../modules/deluge"
  authproxy_host = module.authproxy-default.host
  media-pvc = module.media.claim-name
  domain = local.domain
  tls_secret = local.tls_secrets.default.name
}

module "devpi" {
  source = "../../modules/devpi"
  domain = local.domain
}

module "filebrowser" {
  source = "../../modules/filebrowser"
  authproxy_host = module.authproxy-default.host
  media-pvc = module.media.claim-name
  domain = local.domain
  tls_secret = local.tls_secrets.default.name
}

module "grafana" {
  source = "../../modules/grafana"
  authproxy_host = module.authproxy-default.host
  prometheus_url = "http://${module.prometheus.service}"
  domain = local.domain
  tls_secret = local.tls_secrets.default.name
}

module "grocy" {
  source = "../../modules/grocy"
  authproxy_host = module.authproxy-default.host
  domain = local.domain
  tls_secret = local.tls_secrets.default.name
}

module "hardlinker" {
  source = "../../modules/hardlinker"
  media-pvc = module.media.claim-name
  domain = local.domain
  authproxy_host = module.authproxy-default.host
  tls_secret = local.tls_secrets.default.name
}

module "heimdall" {
  source = "../../modules/heimdall"
  domain = local.domain
  heimdall_apps = [
    # kubectl exec svc/heimdall -c main -- ls /config/www/icons
    {name: "Ceph",        image_url: "https://raw.githubusercontent.com/ceph/ceph/a67d1cf2a7a4031609a5d37baa01ffdfef80e993/src/pybind/mgr/dashboard/frontend/src/assets/Ceph_Logo.svg", url: "https://ceph-dashboard.${local.domain}", color: "#161b1f"},
    {name: "Deluge",      image_url: "", url: "https://${module.deluge.host}",       color: "#161b1f"},
    {name: "Filebrowser", image_url: "", url: "https://${module.filebrowser.host}",  color: "#161b1f"},
    {name: "Grafana",     image_url: "", url: "https://${module.grafana.host}",      color: "#161b1f"},
    {name: "Grocy",       image_url: "", url: "https://${module.grocy.host}",        color: "#161b1f"},
    {name: "Hardlinker",  image_url: "https://icons.iconarchive.com/icons/thehoth/seo/256/seo-chain-link-icon.png", url: "https://hardlinker.${local.domain}", color: "#161b1f"},
    {name: "Jellyfin",    image_url: "", url: "https://${module.jellyfin.host}",     color: "#161b1f"},
    {name: "Keycloak",    image_url: "", url: "https://${module.keycloak.host}",     color: "#161b1f"},
    {name: "Komga",       image_url: "", url: "https://${module.komga.host}",        color: "#161b1f"},
    {name: "Mail",        image_url: "https://www.fastmail.com//static/images/square-logo-icon-white.svg", url: "http://mail.antonpaqu.in", color: "#161b1f"},
    {name: "Metube",      image_url: "https://raw.githubusercontent.com/alexta69/metube/master/favicon/android-chrome-384x384.png", url: "http://${module.metube.host}", color: "#161b1f"},
    {name: "Photoprism",  image_url: "", url: "https://${module.photoprism.host}",   color: "#161b1f"},
    {name: "Prometheus",  image_url: "", url: "https://${module.prometheus.host}",   color: "#161b1f"},
    {name: "Proxmox",     image_url: "", url: "https://10.0.100.177:8006",           color: "#161b1f"},
    {name: "Sonarr",      image_url: "", url: "https://${module.sonarr.host}",       color: "#161b1f"},
    {name: "Tandoor",     image_url: "", url: "https://${module.tandoor.host}",      color: "#161b1f"},
    {name: "Wordpress",   image_url: "", url: "https://${module.blog.host}",         color: "#161b1f"},
  ]
}

module "jellyfin" {
  source = "../../modules/jellyfin"
  authproxy_host = module.authproxy-default.host
  domain = local.domain
  media-pvc = module.media.claim-name
  tls_secret = local.tls_secrets.default.name
}

module "keycloak" {
  depends_on = [module.postgresql]
  domain = local.domain
  source = "../../modules/keycloak"
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

module "komga" {
  source = "../../modules/komga"
  authproxy_host = module.authproxy-default.host
  domain = local.domain
  media-pvc = module.media.claim-name
  tls_secret = local.tls_secrets.default.name
}

module "logserv" {
  # Echoes back the request, basically
  authproxy_host = module.authproxy-default.host
  source = "../../modules/logserv"
  domain = local.domain
  tls_secret = local.tls_secrets.default.name
}

module "mariadb" {
  source = "../../modules/mariadb"
  domain = local.domain
}

module "matrix" {
  source = "../../modules/matrix"
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

module "media" {
  source = "../../modules/media"
}

module "media-srv" {
  source = "../../modules/media_srv"
  domain = local.domain
  media-pvc = module.media.claim-name
}

module "metube" {
  source = "../../modules/metube"
  authproxy_host = module.authproxy-default.host
  domain = local.domain
  media-pvc = module.media.claim-name
  tls_secret = local.tls_secrets.default.name
}

module "photoprism" {
  depends_on = [module.mariadb]
  source = "../../modules/photoprism"
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

module "postgresql" {
  source = "../../modules/postgresql"
}

module "prometheus" {
  source = "../../modules/prometheus"
  domain = local.domain
  tls_secret = local.tls_secrets.default.name
}

module "shell" {
  source = "../../modules/shell"
  media-pvc = module.media.claim-name
  backup-pvc = module.volumes.backup-claim-name
}

module "sonarr" {
  source = "../../modules/sonarr"
  authproxy_host = module.authproxy-default.host
  domain = local.domain
  media-pvc = module.media.claim-name
  tls_secret = local.tls_secrets.default.name
}

module "stable-diffusion" {
  source = "../../modules/stable-diffusion"
  domain = local.domain
  authproxy_host = module.authproxy-default.host
  tls_secret = local.tls_secrets.default.name
}

module "tandoor" {
  source = "../../modules/tandoor"
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

module "volumes" {
  source = "../../modules/volumes"
  backup-size = "1Ti"
}
