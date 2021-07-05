# Remove to init a new cluster, might delete data
module "prep_storage" {
  for_each = var.init_drives ? local.storage : {}
  source = "../../../modules/local_script"
  name = "rook_prep_storage_${each.key}"
  # Use this script to init a new cluster. Warning: will delete data
  script = <<EOF
#! /bin/bash
ssh ${each.value.node} <<ENDSSH
  sudo dd if=/dev/zero of=${each.value.device} bs=4M count=20
ENDSSH
EOF
}

module "prep_meta" {
  count = var.init_drives ? 1 : 0
  source = "../../../modules/local_script"
  name = "rook_prep_meta"
  script = <<EOF
#! /bin/bash
ssh ${local.meta.node} <<ENDSSH
  sudo rm -rf ${local.meta.path}
  sudo mkdir -p ${local.meta.path}
ENDSSH
EOF
}

resource "kubernetes_storage_class" "physical" {
  storage_provisioner = "kubernetes.io/no-provisioner"
  volume_binding_mode = "WaitForFirstConsumer"
  metadata {
    name = "physical"
  }
}

resource "kubernetes_persistent_volume" "physical_pv" {
  for_each = local.storage
  metadata {
    name = each.key
  }
  spec {
    storage_class_name = kubernetes_storage_class.physical.metadata[0].name
    access_modes = ["ReadWriteOnce"]
    capacity = {
      storage: each.value.capacity
    }
    persistent_volume_reclaim_policy = "Retain"
    persistent_volume_source {
      local {
        path = each.value.device
      }
    }
    volume_mode = "Block"
    node_affinity {
      required {
        node_selector_term {
          match_expressions {
            key = "kubernetes.io/hostname"
            operator = "In"
            values = [each.value.node]
          }
        }
      }
    }
  }
}

