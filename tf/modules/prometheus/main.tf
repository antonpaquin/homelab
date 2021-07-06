variable "domain" {
  type = string
  default = "k8s.local"
}

locals {
  namespace = "default"
  host = "prometheus.${var.domain}"
}

locals {
  server_host = local.host
  alertmanager_host = "alertmanager.${local.host}"
  pushgateway_host = "pushgateway.${local.host}"
}

resource "helm_release" "prometheus" {
  repository = "https://prometheus-community.github.io/helm-charts"
  chart = "prometheus"
  version = "14.3.0"

  name = "prometheus"
  namespace = local.namespace

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
        enabled: true
        hosts: [local.server_host]
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

output "host" {
  value = local.host
}

output "service" {
  value = "prometheus-server"
}