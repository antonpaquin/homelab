module "rook" {
  source = "../../../modules/rook/03-StorageClass"
}

module "pv_saver" {
  source = "../../../modules/pv_saver"
}
