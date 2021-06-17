module "flannel" {
  source = "../../modules/flannel"
}

module "coredns" {
  source = "../../modules/coredns"
}

module "nginx" {
  source = "../../modules/nginx"
}

module "rook" {
  source = "../../modules/rook/00-CustomResources"
}
