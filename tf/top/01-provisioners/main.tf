module "nfs" {
  source = "../../modules/app_infra/nfs"
  nfs_root = {
    capacity = "7168Gi"
    hostPath = "/storage/root"
    node = "reimu-00"
    node_ip = "192.168.0.105"
  }
}
