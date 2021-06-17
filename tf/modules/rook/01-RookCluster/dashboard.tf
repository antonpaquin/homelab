variable "domain" {
  type = string
  default = "k8s.local"
}

resource "kubernetes_ingress" "ceph-dashboard" {
  metadata {
    name = "ceph-dashboard"
    namespace = local.namespace
    annotations = {
      "kubernetes.io/ingress.class": "nginx"
    }
  }
  spec {
    rule {
      host = "ceph-dashboard.${var.domain}"
      http {
        path {
          backend {
            service_name = "rook-ceph-mgr-dashboard"
            service_port = 7000
          }
        }
      }
    }
  }
}

