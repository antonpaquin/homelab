locals {
  yomi_ip   = "10.10.10.1"
  chiyo_ip  = "10.10.10.2"
  sakaki_ip = "10.10.10.3"
  osaka_ip  = "10.10.10.4"
}

module "nfs" {
  source = "../../../modules/k8s_infra/nfs-external"
  nfs_node_ip = local.osaka_ip
}

module "nginx" {
  source = "../../../modules/k8s_infra/nginx"
}
