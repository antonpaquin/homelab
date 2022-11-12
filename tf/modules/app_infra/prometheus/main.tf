variable "domain" {
  type = string
}

variable "tls_secret" {
  type = string
  description = "Secret containing a wildcard certificate of the type kubernetes.io/tls"
}

locals {
  namespace = "default"
  host = "prometheus.${var.domain}"
}

locals {
  server_host = local.host
  alertmanager_host = "alertmanager-${local.host}"
  pushgateway_host = "pushgateway-${local.host}"
}

resource "helm_release" "prometheus" {
  wait = false
  wait_for_jobs = false
  repository = "https://prometheus-community.github.io/helm-charts"
  chart = "prometheus"
  version = "14.3.0"

  name = "prometheus"
  namespace = local.namespace
  timeout = 5  # todo: fix

  values =[yamlencode({
    alertmanager: {
      baseURL: "http://${local.alertmanager_host}",
      ingress: {
        enabled: true
        ingressClassName: "nginx"
        hosts: [local.alertmanager_host]
      }
    }
    server: {
      baseURL: "http://${local.server_host}"
      extraFlags: [
        "web.enable-lifecycle",
        "web.enable-admin-api"
      ]
      ingress: {
        enabled: false
      }
    }
    pushgateway: {
      ingress: {
        enabled: true
        hosts: [local.pushgateway_host]
      }
    }
  })]
}

# resource "kubernetes_persistent_volume_claim" "prometheus-server" {
#   # Why is this not auto?
#   metadata {
#     name = "prometheus-server"
#     namespace = local.namespace
#   }
#   spec {
#     access_modes = ["ReadWriteOnce"]
#     resources {
#       requests = {
#         storage = "2Gi"
#       }
#     }
#   }
# }

# resource "kubernetes_persistent_volume_claim" "prometheus-alertmanager" {
#   # Why is this not auto?
#   metadata {
#     name = "prometheus-alertmanager"
#     namespace = local.namespace
#   }
#   spec {
#     access_modes = ["ReadWriteOnce"]
#     resources {
#       requests = {
#         storage = "2Gi"
#       }
#     }
#   }
# }

module "protected_ingress" {
  source = "../../../modules/app_infra/authproxy/protected_ingress"
  host = local.host
  authproxy_host = "authproxy.${var.domain}"
  namespace = local.namespace
  name = "prometheus-server"
  service_name = "prometheus-server"
  service_port = "http"
  tls_secret = var.tls_secret
}

output "host" {
  value = local.host
}

output "service" {
  value = "prometheus-server"
}