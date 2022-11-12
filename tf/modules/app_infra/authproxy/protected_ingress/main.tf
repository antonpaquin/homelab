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
  type = string
  description = "host where the corresponding instance of authproxy will be accessed"
}

variable "tls_secret" {
  type = string
  description = "Secret containing a wildcard certificate of the type kubernetes.io/tls"
}


locals {
  sso_annotations = {
    "nginx.ingress.kubernetes.io/auth-url": "http://${local.auth_service_name}.${local.auth_namespace}.svc.cluster.local/validate"
    "nginx.ingress.kubernetes.io/auth-signin": "https://${var.authproxy_host}/login"
    # "nginx.ingress.kubernetes.io/auth-snippet": "proxy_pass_header Cookie;"
  }
  authproxy_endpoint = "/_authproxy"
  auth_service_name = "authproxy"
  auth_namespace = "default"
}


resource "kubernetes_ingress_v1" "protected_ingress" {
  metadata {
    name = var.name
    namespace = var.namespace
    annotations = merge(local.sso_annotations, var.extra_annotations)
  }
  spec {
    ingress_class_name = "nginx"
    tls {
      secret_name = var.tls_secret
    }
    rule {
      host = var.host
      http {
        path {
          path = local.authproxy_endpoint
          backend {
            service {
              name = local.auth_service_name
              port {
                name = "http"
              }
            }
          }
        }
        path {
          path = "/"
          backend {
            service {
              name = var.service_name
              port {
                name = var.service_port
              }
            }
          }
        }
      }
    }
  }
}

