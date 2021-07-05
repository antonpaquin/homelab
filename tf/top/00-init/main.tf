module "flannel" {
  source = "../../modules/flannel"
}

module "coredns" {
  source = "../../modules/coredns"
}

module "nginx" {
  source = "../../modules/nginx"
}
