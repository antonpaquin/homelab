module "rook" {
  source = "../../../modules/rook/02-RookCluster"
  init_drives = true
}
