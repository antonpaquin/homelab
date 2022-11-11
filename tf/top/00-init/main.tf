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

module "nginx" {
  source = "../../modules/k8s_infra/nginx"
}
