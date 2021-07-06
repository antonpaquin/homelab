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

module "heimdall" {
  source = "../../modules/heimdall"
  heimdall_apps = [
    {name: "Deluge",      image_url: "", url: "http://${module.deluge.host}",      color: "#161b1f"},
    {name: "Filebrowser", image_url: "", url: "http://${module.filebrowser.host}", color: "#161b1f"},
    {name: "Grafana",     image_url: "", url: "http://${module.grafana.host}",     color: "#161b1f"},
    {name: "Jellyfin",    image_url: "", url: "http://${module.jellyfin.host}",    color: "#161b1f"},
    {name: "Komga",       image_url: "", url: "http://${module.komga.host}",       color: "#161b1f"},
    {name: "Prometheus",  image_url: "", url: "http://${module.prometheus.host}",  color: "#161b1f"},
    {name: "Proxmox",     image_url: "", url: "https://10.0.100.177:8006",         color: "#161b1f"},
    {name: "Sonarr",      image_url: "", url: "http://${module.sonarr.host}",      color: "#161b1f"},
    {name: "Metube",      image_url: "https://raw.githubusercontent.com/alexta69/metube/master/favicon/android-chrome-384x384.png", url: "http://${module.metube.host}", color: "#161b1f"},
  ]
}

module "jellyfin" {
  source = "../../modules/jellyfin"
  media-pvc = module.media.claim-name
}

module "komga" {
  source = "../../modules/komga"
  media-pvc = module.media.claim-name
}

module "media" {
  source = "../../modules/media"
}

module "metube" {
  source = "../../modules/metube"
  media-pvc = module.media.claim-name
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
