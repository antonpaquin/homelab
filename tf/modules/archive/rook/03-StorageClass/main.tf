variable "domain" {
  type = string
}

locals {
  namespace = "rook"
  dataPoolName = "rbd0"
  metaPoolName = "rbd0-meta"

  cephfsName = "cephfs1"
}
