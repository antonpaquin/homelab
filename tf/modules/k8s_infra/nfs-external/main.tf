
variable "nfs_node_ip" {
    type = string
}

locals {
  namespace = "kube-system"
  pvc_storage_path = "/k8s-pvc"
}

resource "kubernetes_storage_class" "nfs_client" {
  metadata {
    labels = {
      app = "nfs-subdir-external-provisioner"
    }
    name = "nfs-client"
    annotations = {
      "storageclass.kubernetes.io/is-default-class" = "true"
    }
  }
  storage_provisioner = "cluster.local/nfs-subdir-external-provisioner"
  allow_volume_expansion = true
  reclaim_policy = "Delete"
  volume_binding_mode = "Immediate"
  parameters = {
    "archiveOnDelete" = "true"
  }
}

resource "kubernetes_deployment" "nfs_subdir_external_provisioner" {
  lifecycle {
    ignore_changes = [
      spec[0].template[0].spec[0].container[0].security_context
    ]
  }
  wait_for_rollout = false
  metadata {
    labels = {
      app = "nfs-subdir-external-provisioner"
    }
    name = "nfs-subdir-external-provisioner"
    namespace = local.namespace
  }
  spec {
    replicas = 1
    strategy {
      type = "Recreate"
    }
    selector {
      match_labels = {
        "app" = "nfs-subdir-external-provisioner"
      }
    }
    template {
      metadata {
        labels = {
          "app" = "nfs-subdir-external-provisioner"
        }
      }
      spec {
        service_account_name = kubernetes_service_account.nfs_subdir_exteral_provisioner.metadata[0].name
        container {
          name = "nfs-subdir-external-provisioner"
          image = "k8s.gcr.io/sig-storage/nfs-subdir-external-provisioner:v4.0.2"
          image_pull_policy = "IfNotPresent"
          volume_mount {
            name = "nfs-subdir-external-provisioner-root"
            mount_path = "/persistentvolumes"
          }
          env {
            name = "PROVISIONER_NAME"
            value = "cluster.local/nfs-subdir-external-provisioner"
          }
          env {
            name = "NFS_SERVER"
            value = var.nfs_node_ip
          }
          env {
            name = "NFS_PATH"
            value = local.pvc_storage_path
          }
        }
        volume {
          name = "nfs-subdir-external-provisioner-root"
          nfs {
            server = var.nfs_node_ip
            path = local.pvc_storage_path
          }
        }
      }
    }
  }
}

resource "kubernetes_service_account" "nfs_subdir_exteral_provisioner" {
  metadata {
    labels = {
      "app" = "nfs-subdir-external-provisioner"
    }
    name = "nfs-subdir-external-provisioner"
    namespace = local.namespace
  }
}

resource "kubernetes_cluster_role" "nfs_subdir_external_provisioner_runner" {
  metadata {
    labels = {
      app = "nfs-subdir-external-provisioner"
    }
    name = "nfs-subdir-external-provisioner-runner"
  }
  rule {
    api_groups = [""]
    resources = ["nodes"]
    verbs = ["get", "list", "watch"]
  }
  rule {
    api_groups = [""]
    resources = ["persistentvolumes"]
    verbs = ["get", "list", "watch", "create", "delete"]
  }
  rule {
    api_groups = [""]
    resources = ["persistentvolumeclaims"]
    verbs = ["get", "list", "watch", "update"]
  }
  rule {
    api_groups = ["storage.k8s.io"]
    resources = ["storageclasses"]
    verbs = ["get", "list", "watch"]
  }
  rule {
    api_groups = [""]
    resources = ["events"]
    verbs = ["create", "update", "patch"]
  }
}

resource "kubernetes_cluster_role_binding" "run_nfs_subdir_external_provisioner" {
  metadata {
    labels = {
      app = "nfs-subdir-external-provisioner"
    }
    name = "run-nfs-subdir-external-provisioner"
  }
  subject {
    kind = "ServiceAccount"
    name = kubernetes_service_account.nfs_subdir_exteral_provisioner.metadata[0].name
    namespace = kubernetes_service_account.nfs_subdir_exteral_provisioner.metadata[0].namespace
  }
  role_ref {
    kind = "ClusterRole"
    name = kubernetes_cluster_role.nfs_subdir_external_provisioner_runner.metadata[0].name
    api_group = "rbac.authorization.k8s.io"
  }
}

resource "kubernetes_role" "leader_locking_nfs_subdir_external_provisioner" {
  metadata {
    labels = {
      app = "nfs-subdir-external-provisioner"
    }
    name = "leader-locking-nfs-subdir-external-provisioner"
    namespace = local.namespace
  }
  rule {
    api_groups = [""]
    resources = ["endpoints"]
    verbs = ["get", "list", "watch", "create", "update", "patch"]
  }
}

resource "kubernetes_role_binding" "leader_locking_nfs_subdir_external_provisioner" {
  metadata {
    labels = {
      app = "nfs-subdir-external-provisioner"
    }
    name = "leader-locking-nfs-subdir-external-provisioner"
    namespace = local.namespace
  }
  subject {
    kind = "ServiceAccount"
    name = kubernetes_service_account.nfs_subdir_exteral_provisioner.metadata[0].name
    namespace = kubernetes_service_account.nfs_subdir_exteral_provisioner.metadata[0].namespace  # chart specifies default -- why?
  }
  role_ref {
    kind = "Role"
    name = kubernetes_role.leader_locking_nfs_subdir_external_provisioner.metadata[0].name
    api_group = "rbac.authorization.k8s.io"
  }
}
