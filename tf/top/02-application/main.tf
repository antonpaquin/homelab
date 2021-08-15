locals {
  secret =yamldecode(file("../../secret.yaml"))
}

module "authproxy-ceph" {
  source = "../../modules/authproxy/app"
  keycloak-oidc = {
    client-id = "authproxy-ceph-oidc"
    client-secret = local.secret["keycloak"]["authproxy-ceph-oidc-secret"]
  }
  host = "authproxy-ceph.k8s.local"
  namespace = "rook"

}

module "authproxy-default" {
  source = "../../modules/authproxy/app"
  keycloak-oidc = {
    client-id = "authproxy-oidc"
    client-secret = local.secret["keycloak"]["authproxy-oidc-secret"]
  }
  host = "authproxy.k8s.local"
  namespace = "default"
}

module "bind9" {
  source = "../../modules/bind9"
  reimu-ingress-ip = "10.0.4.64"
}

module "cadvisor" {
  source = "../../modules/cadvisor"
}

module "dad-ffmpeg" {
  source = "../../modules/dad-ffmpeg"
}

module "deluge" {
  source = "../../modules/deluge"
  media-pvc = module.media.claim-name
}

module "filebrowser" {
  source = "../../modules/filebrowser"
  media-pvc = module.media.claim-name
}

module "grafana" {
  source = "../../modules/grafana"
  prometheus_url = "http://${module.prometheus.service}"
}

module "hardlinker" {
  source = "../../modules/hardlinker"
  media-pvc = module.media.claim-name
}

module "heimdall" {
  source = "../../modules/heimdall"
  heimdall_apps = [
    # kubectl exec svc/heimdall -c main -- ls /config/www/icons
    {name: "Ceph",        image_url: "https://raw.githubusercontent.com/ceph/ceph/a67d1cf2a7a4031609a5d37baa01ffdfef80e993/src/pybind/mgr/dashboard/frontend/src/assets/Ceph_Logo.svg", url: "http://ceph-dashboard.k8s.local", color: "#161b1f"},
    {name: "Deluge",      image_url: "", url: "http://${module.deluge.host}",       color: "#161b1f"},
    {name: "Filebrowser", image_url: "", url: "http://${module.filebrowser.host}",  color: "#161b1f"},
    {name: "Grafana",     image_url: "", url: "http://${module.grafana.host}",      color: "#161b1f"},
    {name: "Jellyfin",    image_url: "", url: "http://${module.jellyfin.host}",     color: "#161b1f"},
    {name: "Keycloak",    image_url: "", url: "http://${module.keycloak.host}", color: "#161b1f"},
    {name: "Komga",       image_url: "", url: "http://${module.komga.host}",        color: "#161b1f"},
    {name: "Mail",        image_url: "https://www.fastmail.com//static/images/square-logo-icon-white.svg", url: "http://mail.antonpaqu.in", color: "#161b1f"},
    {name: "Metube",      image_url: "https://raw.githubusercontent.com/alexta69/metube/master/favicon/android-chrome-384x384.png", url: "http://${module.metube.host}", color: "#161b1f"},
    {name: "Photoprism",  image_url: "", url: "http://${module.photoprism.host}",   color: "#161b1f"},
    {name: "Prometheus",  image_url: "", url: "http://${module.prometheus.host}",   color: "#161b1f"},
    {name: "Proxmox",     image_url: "", url: "https://10.0.100.177:8006",          color: "#161b1f"},
    {name: "Sonarr",      image_url: "", url: "http://${module.sonarr.host}",       color: "#161b1f"},
  ]
}

module "jellyfin" {
  source = "../../modules/jellyfin"
  media-pvc = module.media.claim-name
}

module "keycloak" {
  source = "../../modules/keycloak"
  keycloak-admin-password = local.secret["keycloak"]["admin"]
  keycloak-db = {
    vendor = "postgres"
    user = module.postgresql.user
    password = module.postgresql.password
    host = module.postgresql.host
    port = module.postgresql.port
  }
}

module "komga" {
  source = "../../modules/komga"
  media-pvc = module.media.claim-name
}

module "mariadb" {
  source = "../../modules/mariadb"
}

module "media" {
  source = "../../modules/media"
}

module "metube" {
  source = "../../modules/metube"
  media-pvc = module.media.claim-name
}

module "photoprism" {
  source = "../../modules/photoprism"
  database = {
    username = module.mariadb.user
    password = module.mariadb.password
    host = module.mariadb.service
    port = module.mariadb.port
    dbname = "photoprism"
  }
  media-pvc = module.media.claim-name
}

module "postgresql" {
  source = "../../modules/postgresql"
}

module "prometheus" {
  source = "../../modules/prometheus"
}

module "shell" {
  source = "../../modules/shell"
  media-pvc = module.media.claim-name
}

module "sonarr" {
  source = "../../modules/sonarr"
  media-pvc = module.media.claim-name
}
