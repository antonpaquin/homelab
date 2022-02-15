variable "backup-size" {
  type = string
  description = "Size of the backup volume"
}

locals {
  namespace = "default"
}


# Todo: put media in here as well


resource "kubernetes_persistent_volume_claim" "backup" {
  lifecycle {prevent_destroy = true}
  metadata {
    name = "backup"
    namespace = local.namespace
  }
  spec {
    access_modes = ["ReadWriteOnce"]
    storage_class_name = "ceph-block"
    resources {
      requests = {
        storage = var.backup-size
      }
    }
  }
}

output "backup-claim-name" {
  value = kubernetes_persistent_volume_claim.backup.metadata[0].name
}
