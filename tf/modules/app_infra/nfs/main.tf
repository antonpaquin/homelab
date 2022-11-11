variable "nfs_root" {
  type = object({
    node = string
    node_ip = string
    hostPath = string
    capacity = string
  })
}

locals {
  namespace = "kube-system"
  # storage_class_name = kubernetes_storage_class.physical.metadata[0].name
  physical_storage_class_name = "physical"  # todo: replace w above when swapover complete / unwinding rook 
  node_port = 2049
}

# todo: automate bindmounts
# (/library -> media:/library)
# does this need to be done on reboot?
# should I set up some kind of fstab structure in the storage root?
# currently having some trouble (?) when I specify the mount in reimu-00, but when created in the nfs container itself it works fine
#
# probably easiest reliable structure is an fstab and add that to the nfs boot script

resource "kubernetes_config_map" "nfs_exports" {
  metadata {
    name = "nfs-exports"
    namespace = local.namespace
  }
  data = {
    "exports" = <<EOF
/nfs *(rw,fsid=0,async,no_subtree_check,no_auth_nlm,insecure,no_root_squash,crossmnt)
EOF
  }
}

resource "kubernetes_persistent_volume" "physical_pv" {
  metadata {
    name = "nfs-root"
    # pv's are not namespaced
  }
  spec {
    # storage_class_name = kubernetes_storage_class.physical.metadata[0].name
    storage_class_name = local.physical_storage_class_name
    access_modes = ["ReadWriteOnce"]
    capacity = {
      storage: var.nfs_root.capacity
    }
    persistent_volume_reclaim_policy = "Retain"
    persistent_volume_source {
      local {
        path = var.nfs_root.hostPath
      }
    }
    volume_mode = "Filesystem"  # Trust the mount
    node_affinity {
      required {
        node_selector_term {
          match_expressions {
            key = "kubernetes.io/hostname"
            operator = "In"
            values = [var.nfs_root.node]
          }
        }
      }
    }
  }
}

resource "kubernetes_persistent_volume_claim" "nfs" {
  metadata {
    name = "nfs-root"
    namespace = local.namespace
  }
  spec {
    access_modes = ["ReadWriteOnce"]
    resources {
      requests = {
        storage = var.nfs_root.capacity
      }
    }
    storage_class_name = local.physical_storage_class_name
    volume_name = kubernetes_persistent_volume.physical_pv.metadata[0].name
  }
}

resource "kubernetes_deployment" "nfs" {
  metadata {
    name = "nfs"
    namespace = local.namespace
  }
  spec {
    selector {
      match_labels = {
        app = "nfs"
      }
    }
    template {
      metadata {
        labels = {
          app = "nfs"
        }
      }
      spec {
        container {
          name = "main"
          image = "itsthenetwork/nfs-server-alpine:12"
          env {
            name = "SHARED_DIRECTORY"
            value = "/nfs"
          }
          security_context {
            privileged = true
          }
          volume_mount {
            name = "nfs-root"
            mount_path = "/nfs"
            mount_propagation = "HostToContainer"
          }
          volume_mount {
            name = "exports-config"
            mount_path = "/etc/exports"
            sub_path = "exports"
          }
        }
        volume {
          name = "nfs-root"
          persistent_volume_claim {
            claim_name = kubernetes_persistent_volume_claim.nfs.metadata[0].name
          }
        }
        volume {
          name = "exports-config"
          config_map {
            name = kubernetes_config_map.nfs_exports.metadata[0].name
          }
        }
      }
    }
  }
}

resource "kubernetes_service" "nfs" {
  metadata {
    name = "nfs"
    namespace = local.namespace
  }
  spec {
    selector = {
      app = "nfs"
    }
    port {
      port = 2049
      name = "nfs"
      node_port = local.node_port
    }
    type = "NodePort"
  }
}

resource "helm_release" "nfs-provisioner" {
  # todo un-helm this?
  repository = "https://kubernetes-sigs.github.io/nfs-subdir-external-provisioner"
  chart = "nfs-subdir-external-provisioner"
  name = "nfs-subdir-external-provisioner"
  namespace = local.namespace
  version = "4.0.17"

  values = [yamlencode({
    nfs = {
      server = var.nfs_root.node_ip
      path = "/k8s-pvc" 
    }
  })]
}
