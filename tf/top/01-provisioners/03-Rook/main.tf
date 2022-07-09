module "rook" {
  source = "../../../modules/rook/03-StorageClass"
  domain = "antonpaqu.in"
}

module "pv_saver" {
  source = "../../../modules/pv_saver"
}
