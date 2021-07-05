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
  namespace = kubernetes_namespace.rook-ceph.metadata[0].name
  repository = "https://charts.rook.io/release"
}
