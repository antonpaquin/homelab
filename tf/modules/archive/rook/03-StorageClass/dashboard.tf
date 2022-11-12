locals {
  future_authproxy_host = "authproxy.${var.domain}"
  future_tls_secret_name = "tls-cert"
}

resource "kubernetes_ingress_v1" "ceph-dashboard" {
  metadata {
    name = "ceph-dashboard-public"
    namespace = local.namespace
    annotations = {
      "kubernetes.io/ingress.class": "nginx"
    }
  }
  spec {
    ingress_class_name = "nginx"
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
  # Won't actually come alive until authproxy is up in step 02-application
  source = "../../../modules/app_infra/authproxy/protected_ingress"
  host = "ceph-dashboard.${var.domain}"
  name = "ceph-dashboard"
  namespace = local.namespace
  service_name = "rook-ceph-mgr-dashboard"
  service_port = "http-dashboard"

  authproxy_host = local.future_authproxy_host
  tls_secret = local.future_tls_secret_name
}

module "authproxy_service" {
  source = "../../../modules/app_infra/authproxy/protected_ingress"
  namespace = local.namespace
}
