variable "domain" {
  type = string
  default = "k8s.local"
}

variable "prometheus_url" {
  type = string
}

locals {
  namespace = "default"
  host = "grafana.${var.domain}"
  admin_username = "admin"
  admin_password = "cirno9ball"
}

locals {
  dashboards = {
    node-exporter: {
      gnetId: 1860
      revision: 23
      datasource: "Prometheus"
    }
    ingress-nginx: {
      gnetId: 9614
      revision: 1
      datasource: "Prometheus"
    }
    coredns: {
      gnetId: 5926
      revision: 1
      datasource: "Prometheus"
    }
    ceph: {
      gnetId: 2842
      revision: 14
      datasource: "Prometheus"
    }
    cadvisor: {
      gnetId: 14282
      revision: 1
      datasource: "Prometheus"
    }
  }
}

resource "helm_release" "grafana" {
  repository = "https://grafana.github.io/helm-charts"
  chart = "grafana"
  version = "6.13.6"

  name = "grafana"
  namespace = local.namespace

  values = [yamlencode({
    testFramework: {
      enabled: false
    }
    ingress: {
      enabled: true
      hosts: [local.host]
    }
    admin: {
      existingSecret: kubernetes_secret.grafana-credentials.metadata[0].name
      userKey: "user"
      passwordKey: "password"
    }
    "grafana.ini": {
      dashboards: {
        default_home_dashboard_path = "/var/lib/grafana/dashboards/default/node-exporter.json"
      }
    }
    datasources: {
      "datasources.yaml": {
        apiVersion: 1
        datasources: [
          {
            name: "Prometheus"
            type: "prometheus"
            url: var.prometheus_url
            isDefault: true
          }
        ]
      }
    }
    dashboardProviders: {
      "dashboardproviders.yaml": {
        apiVersion: 1
        providers: [{
          name: "default"
          orgId: 1
          folder: ""
          type: "file"
          disableDeletion: true
          editable: false
          options: {
            path: "/var/lib/grafana/dashboards/default"
          }
        }]
      }
    }
    dashboards: {
      default: local.dashboards
    }
  })]
}

resource "kubernetes_secret" "grafana-credentials" {
  # TODO: SSO
  metadata {
    name = "grafana-admin-credentials"
    namespace = local.namespace
  }
  data = {
    user: local.admin_username
    password: local.admin_password
  }
}

output "host" {
  value = local.host
}
