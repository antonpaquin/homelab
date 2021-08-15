resource "kubernetes_ingress" "ceph-dashboard" {
  metadata {
    name = "ceph-dashboard-public"
    namespace = local.namespace
    annotations = {
      "kubernetes.io/ingress.class": "nginx"
    }
  }
  spec {
    rule {
      host = "ceph-dashboard-public.${var.domain}"
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

module "authproxy_ingress" {
  # Won't actually come alive until authproxy-ceph is up in step 02-application
  source = "../../../modules/authproxy/protected_ingress"
  host = "ceph-dashboard.${var.domain}"
  name = "ceph-dashboard"
  namespace = local.namespace
  service_name = "rook-ceph-mgr-dashboard"
  service_port = "http-dashboard"
  authproxy_host = "authproxy-ceph.k8s.local"
}

