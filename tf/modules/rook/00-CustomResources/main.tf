resource "kubernetes_namespace" "rook-ceph" {
  metadata {
    name = "rook-ceph"
  }
}

resource "helm_release" "rook" {
  depends_on = [kubernetes_namespace.rook-ceph]

  chart = "rook-ceph"
  name = "rook-ceph"
  namespace = "rook-ceph"
  repository = "https://charts.rook.io/release"
}
