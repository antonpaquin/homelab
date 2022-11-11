# module "calico" {
#  # Does calico work? then I actually need to put in the effort to create this module
#   source = "../../modules/calico"
# }

locals {
  reimu_ip = "192.168.0.105"
}

module "coredns" {
  source = "../../modules/k8s_infra/coredns"
  # Allow reimu to be used as DNS (requires bind9 module later, but that's OK)
  coredns-snippet = <<EOF
k8s.local {
    forward . ${local.reimu_ip}
}
EOF
}

module "nfs" {
  source = "../../modules/k8s_infra/nfs"
  nfs_root = {
    capacity = "7168Gi"
    host_path = "/storage/root"
    node = "reimu-00"
    node_ip = "192.168.0.105"
  }
}

module "nginx" {
  source = "../../modules/k8s_infra/nginx"
}

module "nvidia" {
  source = "../../modules/k8s_infra/nvidia"
}