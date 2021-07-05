variable "domain" {
  type = string
  default = "k8s.local"
}

locals {
  namespace = "rook"
  dataPoolName = "rbd0"
  metaPoolName = "rbd0-meta"
}
