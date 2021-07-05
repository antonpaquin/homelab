module "bind9" {
  source = "../../modules/bind9"
  reimu-ingress-ip = "10.0.4.64"
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

module "heimdall" {
  source = "../../modules/heimdall"
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

module "shell" {
  source = "../../modules/shell"
  media-pvc = module.media.claim-name
}

module "sonarr" {
  source = "../../modules/sonarr"
  media-pvc = module.media.claim-name
}
