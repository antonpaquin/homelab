variable "name" {
  type = string
  description = "Name of the ingress"
}

variable "namespace" {
  type = string
  description = "Namespace for the service and ingress"
}

variable "service_name" {
  type = string
  description = "Name of the service to be protected"
}

variable "service_port" {
  type = string
  description = "Target port for the service to be protected"
}

variable "host" {
  type = string
  description = "Name where the ingress will be exposed"
}

variable "extra_annotations" {
  default = {}
  type = map(string)
  description = "More annotations to attach to the ingress"
}

variable "authproxy_host" {
  default = "authproxy.k8s.local"
  type = string
  description = "host where the corresponding instance of authproxy will be accessed"
}


locals {
  sso_annotations = {
    "nginx.ingress.kubernetes.io/auth-url": "http://${var.authproxy_host}/validate"
    "nginx.ingress.kubernetes.io/auth-signin": "http://${var.authproxy_host}/login"
    # "nginx.ingress.kubernetes.io/auth-snippet": "proxy_pass_header Cookie;"
  }
  authproxy_endpoint = "/_authproxy"
  auth_service_name = "authproxy"
}


resource "kubernetes_ingress" "protected_ingress" {
  metadata {
    name = var.name
    namespace = var.namespace
    annotations = merge(local.sso_annotations, var.extra_annotations)
  }
  spec {
    rule {
      host = var.host
      http {
        path {
          path = local.authproxy_endpoint
          backend {
            service_name = local.auth_service_name
            service_port = "http"
          }
        }
        path {
          path = "/"
          backend {
            service_name = var.service_name
            service_port = var.service_port
          }
        }
      }
    }
  }
}

