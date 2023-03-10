module "heimdall" {
  source = "../../../modules/app/heimdall"
  domain = local.domain
  heimdall_apps = [
    # kubectl exec svc/heimdall -c main -- ls /config/www/icons
    {name: "Deluge",      image_url: "", url: "https://${module.deluge.host}",       color: "#161b1f"},
    {name: "Filebrowser", image_url: "", url: "https://${module.filebrowser.host}",  color: "#161b1f"},
    {name: "Keycloak",    image_url: "", url: "https://${module.keycloak.host}",     color: "#161b1f"},
    {name: "Metube",      image_url: "https://raw.githubusercontent.com/alexta69/metube/master/favicon/android-chrome-384x384.png", url: "http://${module.metube.host}", color: "#161b1f"},
    {name: "Photoprism",  image_url: "", url: "https://${module.photoprism.host}",   color: "#161b1f"},
  ]
}
