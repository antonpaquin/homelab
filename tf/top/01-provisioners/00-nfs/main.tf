module "nfs" {
  source = "../../../modules/nfs"
  nfs_root = {
    capacity = "3726Gi"
    hostPath = "/storage/root"
    node = "reimu-00"
    node_ip = "192.168.0.104"
  }
}
