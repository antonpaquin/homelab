variable "namespace" {
    type = string
}

variable "authproxy_namespace" {
    default = "default"
    type = string
}

resource "kubernetes_service" "authproxy" {
    metadata {
        name = "authproxy"
        namespace = var.namespace
    }
    spec {
        type = "ExternalName"
        external_name = "authproxy.${var.authproxy_namespace}.svc.cluster.local"
        port {
            port = 80
        }
    }
}