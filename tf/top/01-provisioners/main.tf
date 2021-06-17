module "rook-cluster" {
  source = "../../modules/rook/01-RookCluster"
  init_drives = false
}
