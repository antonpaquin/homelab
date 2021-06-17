locals {
  namespace = "default"
}

resource "kubernetes_persistent_volume_claim" "media" {
  lifecycle {prevent_destroy = true}
  metadata {
    name = "media"
    namespace = local.namespace
  }
  spec {
    access_modes = ["ReadWriteOnce"]
    storage_class_name = "ceph-block"
    resources {
      requests = {
        storage = "2Ti"
      }
    }
  }
}

output "claim-name" {
  value = kubernetes_persistent_volume_claim.media.metadata[0].name
}