module "bind9" {
  source = "../../modules/bind9"
  reimu-ingress-ip = "10.0.100.92"
}

module "deluge" {
  source = "../../modules/deluge"
  media-pvc = module.media.claim-name
}

module "filebrowser" {
  source = "../../modules/filebrowser"
  media-pvc = module.media.claim-name
}

module "heimdall" {
  source = "../../modules/heimdall"
}

module "mango" {
  source = "../../modules/mango"
  media-pvc = module.media.claim-name
}

module "media" {
  source = "../../modules/media"
}

# module "tachidesk" {
#   source = "../../modules/tachidesk"
#   media-pvc = module.media.claim-name
# }
