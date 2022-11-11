locals {
  namespace = "rook"
  image = "antonpaquin/misc:pv-saver"
  node_name = "hakurei"
}

resource "kubernetes_service" "pv-saver" {
  metadata {
    name = "pv-saver"
    namespace = local.namespace
  }
  spec {
    port {
      port = 1
    }
  }
}

resource "kubernetes_service_account" "pv-saver" {
  metadata {
    name = "pv-saver"
    namespace = local.namespace
  }
}

resource "kubernetes_cluster_role" "pv-saver" {
  metadata {
    name = "pv-saver"
  }
  rule {
    verbs = ["*"]
    api_groups = [""]
    resources = ["persistentvolumes"]
  }
}

resource "kubernetes_cluster_role_binding" "pv-saver" {
  metadata {
    name = "pv-saver"
  }
  role_ref {
    api_group = "rbac.authorization.k8s.io"
    kind = "ClusterRole"
    name = kubernetes_cluster_role.pv-saver.metadata[0].name
  }
  subject {
    kind = "ServiceAccount"
    name = kubernetes_service_account.pv-saver.metadata[0].name
    namespace = kubernetes_service_account.pv-saver.metadata[0].namespace
  }
}

resource "kubernetes_role" "pv-saver" {
  metadata {
    name = "pv-saver"
    namespace = local.namespace
  }
  rule {
    verbs = ["list", "create"]
    api_groups = [""]
    resources = ["configmaps"]
  }
}

resource "kubernetes_role_binding" "pv-saver" {
  metadata {
    name = "pv-saver"
    namespace = local.namespace
  }
  role_ref {
    api_group = "rbac.authorization.k8s.io"
    kind = "Role"
    name = kubernetes_role.pv-saver.metadata[0].name
  }
  subject {
    kind = "ServiceAccount"
    name = kubernetes_service_account.pv-saver.metadata[0].name
    namespace = kubernetes_service_account.pv-saver.metadata[0].namespace
  }
}

resource "kubernetes_stateful_set" "pv-saver" {
  metadata {
    name = "pv-saver"
    namespace = local.namespace
  }
  spec {
    service_name = kubernetes_service.pv-saver.metadata[0].name
    selector {
      match_labels = {
        app = "pv-saver"
      }
    }
    template {
      metadata {
        labels = {
          app = "pv-saver"
        }
      }
      spec {
        service_account_name = kubernetes_cluster_role.pv-saver.metadata[0].name
        node_name = local.node_name
        container {
          name = "main"
          image = local.image
          image_pull_policy = "Always"
          args = [
            "--interval=900",
            "--storage-path=/data/pv",
            "--storage-class=ceph-block"
          ]
          volume_mount {
            name = "pv"
            mount_path = "/data/pv"
          }
        }
        volume {
          name = "pv"
          host_path {
            path = "/data/persistent/ceph-pv"
          }
        }
      }
    }
  }
}
