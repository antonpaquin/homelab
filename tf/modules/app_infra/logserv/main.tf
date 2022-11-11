variable "domain" {
  type = string
}

variable "authproxy_host" {
  type = string
  description = "Authproxy host (for protected ingress)"
}

variable "tls_secret" {
  type = string
  description = "Name of secret where the TLS certificate is located"
}

locals {
  namespace = "default"
  host = "logserv.${var.domain}"
}

resource "kubernetes_deployment" "logserv" {
  metadata {
    name = "logserv"
    namespace = local.namespace
  }
  spec {
    selector {
      match_labels = {
        app = "logserv"
      }
    }
    template {
      metadata {
        labels = {
          app = "logserv"
        }
      }
      spec {
        container {
          name = "main"
          image = "docker.io/antonpaquin/misc:logserv"
        }
      }
    }
  }
}

resource "kubernetes_service" "logserv" {
  metadata {
    name = "logserv"
    namespace = local.namespace
  }
  spec {
    selector = {
      app = "logserv"
    }
    port {
      port = 3000
      name = "http"
    }
  }
}

module "protected_ingress" {
  source = "../../../modules/app_infra/authproxy/protected_ingress"
  host = local.host
  authproxy_host = var.authproxy_host
  name = "logserv"
  namespace = local.namespace
  service_name = kubernetes_service.logserv.metadata[0].name
  service_port = "http"
  extra_annotations = {
    "nginx.ingress.kubernetes.io/proxy-send-timeout": 3600
    "nginx.ingress.kubernetes.io/proxy-read-timeout": 3600
    "nginx.ingress.kubernetes.io/proxy-body-size": "8192m"
    "nginx.ingress.kubernetes.io/configuration-snippet": join("\n", [
      "auth_request_set $auth_resp_user $upstream_http_x_authproxy_user;",
      "proxy_set_header X-User $auth_resp_user;"
    ])
  }
  tls_secret = var.tls_secret
}

output "host" {
  value = local.host
}