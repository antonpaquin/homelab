locals {
  namespace = "default"
}

variable "backup-size" {
  type = string
  description = "Size of the backup volume"
}

resource "kubernetes_persistent_volume_claim" "backup" {
  lifecycle {prevent_destroy = true}
  metadata {
    name = "backup"
    namespace = local.namespace
  }
  spec {
    access_modes = ["ReadWriteOnce"]
    storage_class_name = "nfs-client"
    resources {
      requests = {
        storage = var.backup-size
      }
    }
  }
}

resource "kubernetes_persistent_volume_claim" "media" {
  lifecycle {prevent_destroy = true}
  metadata {
    name = "media"
    namespace = local.namespace
  }
  spec {
    access_modes = ["ReadWriteOnce"]
    storage_class_name = "nfs-client"
    resources {
      requests = {
        storage = "2Ti"
      }
    }
  }
}

resource "kubernetes_persistent_volume_claim" "huggingface" {
  lifecycle {prevent_destroy = true}
  metadata {
    name = "huggingface"
    namespace = local.namespace
  }
  spec {
    access_modes = ["ReadWriteOnce"]
    storage_class_name = "nfs-client"
    resources {
      requests = {
        storage = "100Gi"
      }
    }
  }
}

output "media-claim-name" {
  value = kubernetes_persistent_volume_claim.media.metadata[0].name
}

output "backup-claim-name" {
  value = kubernetes_persistent_volume_claim.backup.metadata[0].name
}

output "huggingface-claim-name" {
  value = kubernetes_persistent_volume_claim.huggingface.metadata[0].name
}