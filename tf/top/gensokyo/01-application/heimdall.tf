module "heimdall" {
  source = "../../../modules/app/heimdall"
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
