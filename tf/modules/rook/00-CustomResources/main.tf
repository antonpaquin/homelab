locals {
  namespace = "rook"
}

resource "kubernetes_namespace" "rook-ceph" {
  metadata {
    name = local.namespace
  }
}

resource "helm_release" "rook" {
  depends_on = [kubernetes_namespace.rook-ceph]

  chart = "rook-ceph"
  name = "rook-ceph"
  version = "1.6.7"  # pinned in a fit of rage, mistaking the source of the error. Can probably be unpinned on next reset
  namespace = kubernetes_namespace.rook-ceph.metadata[0].name
  repository = "https://charts.rook.io/release"
}
