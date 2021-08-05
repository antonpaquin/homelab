variable "init_drives" {
  type = bool
  description = "True to wipe HDDs and reset storage"
}

module "rook" {
  source = "../../../modules/rook/02-RookCluster"
  init_drives = var.init_drives
}
